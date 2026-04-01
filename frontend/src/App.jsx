import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Link, Route, Routes, useLocation, useNavigate, useSearchParams } from "react-router-dom";

const AUTO_SCRAPE_INTERVAL_MS = 5 * 60 * 1000;

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1], delay }
  })
};

const sectionStagger = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08
    }
  }
};

const featureCards = [
  {
    title: "Field search",
    text: "Start with a specific role family and narrow the live job pipeline before review."
  },
  {
    title: "Dynamic outputs",
    text: "Summary, cover letter, and fit scoring update against the selected role."
  },
  {
    title: "Live market refresh",
    text: "Refresh job sources, inspect coverage, and review the latest inventory from one workspace."
  },
  {
    title: "Review surface",
    text: "Check match evidence and generated content before moving to application prep."
  }
];

const workflowSteps = [
  "Choose your target field or role family.",
  "Pull fresh jobs from the enabled sources.",
  "Upload a resume once and keep the profile active.",
  "Review dynamic summaries, cover letters, and scored matches per job."
];

function formatNumber(value) {
  if (value === null || value === undefined) return "0";
  return new Intl.NumberFormat().format(value);
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function formatTime(value) {
  if (!value) return "Not yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not yet";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function playNotificationTone() {
  try {
    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextCtor) return;
    const ctx = new AudioContextCtor();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
    gainNode.gain.setValueAtTime(0.0001, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.07, ctx.currentTime + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.45);
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.45);
    oscillator.onended = () => {
      ctx.close().catch(() => {});
    };
  } catch {
    // Best-effort only. Browsers may block autoplayed audio until the user interacts.
  }
}

function sendBrowserNotification(title, body) {
  if (typeof window === "undefined" || !("Notification" in window) || Notification.permission !== "granted") {
    return;
  }

  const notification = new Notification(title, {
    body,
    tag: "jobintel-live-scrape",
    renotify: true
  });
  notification.onclick = () => window.focus();
}

async function requestNotificationAccess() {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return "unsupported";
  }
  return Notification.requestPermission();
}

function Shell({ children }) {
  const location = useLocation();
  const isDashboard = location.pathname === "/dashboard";

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brandmark" to="/">
          <span className="brandmark-orb" />
          <div>
            <strong>JobIntel</strong>
            <span>Field-guided job intelligence</span>
          </div>
        </Link>
        <nav className="topnav">
          {isDashboard ? (
            <>
              <a href="#search-section">Search</a>
              <a href="#jobs-section">Jobs</a>
              <a href="#market-section">Market</a>
              <a href="#outputs-section">Outputs</a>
            </>
          ) : (
            <>
              <a href="#features">Features</a>
              <a href="#workflow">Workflow</a>
              <Link to="/dashboard">Dashboard</Link>
            </>
          )}
        </nav>
        <Link className="button button-primary" to={location.pathname === "/dashboard" ? "/" : "/dashboard"}>
          {location.pathname === "/dashboard" ? "View Landing" : "Open Dashboard"}
        </Link>
      </header>
      {children}
    </div>
  );
}

function LandingPage() {
  const navigate = useNavigate();
  const [fieldInput, setFieldInput] = useState("AI engineer");
  const [stats, setStats] = useState(null);
  const [sourceData, setSourceData] = useState(null);

  useEffect(() => {
    let cancelled = false;

    fetchJson("/api/stats")
      .then((data) => {
        if (!cancelled) {
          setStats(data.stats);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStats(null);
        }
      });

    fetchJson("/api/sources")
      .then((data) => {
        if (!cancelled) {
          setSourceData(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSourceData(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const metricItems = [
    { label: "Jobs indexed", value: formatNumber(stats?.jobs_scraped ?? 0) },
    { label: "Strong matches", value: formatNumber(stats?.strong_matches ?? 0) },
    { label: "Sources active", value: formatNumber(stats?.sources_in_catalog ?? 0) },
    { label: "Generated resumes", value: formatNumber(stats?.generated_resumes ?? 0) }
  ];
  const sourceHighlights = (sourceData?.last_scrape?.sources || []).slice(0, 4);
  const platformHighlights = [
    "Field-based search across live sources",
    "Dynamic summary and cover-letter generation",
    "Resume-to-job matching with evidence",
    "Source status and scrape visibility"
  ];

  return (
    <Shell>
      <main className="landing-page">
        <section className="hero-grid">
          <motion.div className="hero-copy" initial="hidden" animate="show" variants={sectionStagger}>
            <motion.p className="eyebrow" variants={fadeUp} custom={0}>
              Job search workspace
            </motion.p>
            <motion.h1 variants={fadeUp} custom={0.05}>
              Field-based job search with tailored application output.
            </motion.h1>
            <motion.p className="hero-subtitle" variants={fadeUp} custom={0.1}>
              Search by field, refresh the market, and keep resume fit, summary, and cover letter aligned to the selected job.
            </motion.p>
            <motion.form
              className="hero-search"
              variants={fadeUp}
              custom={0.15}
              onSubmit={(event) => {
                event.preventDefault();
                navigate(`/dashboard?field=${encodeURIComponent(fieldInput.trim())}`);
              }}
            >
              <label htmlFor="field-search" className="sr-only">
                Search field
              </label>
              <input
                id="field-search"
                value={fieldInput}
                onChange={(event) => setFieldInput(event.target.value)}
                placeholder="Search a field like Backend, Data, AI, DevOps..."
              />
              <button className="button button-primary" type="submit">
                Search
              </button>
            </motion.form>
            <motion.div className="hero-actions" variants={fadeUp} custom={0.2}>
              <Link className="button button-primary" to="/dashboard">
                Launch workspace
              </Link>
              <a className="button button-secondary" href="#features">
                Explore features
              </a>
            </motion.div>
          </motion.div>

          <motion.div
            className="hero-panel"
            initial={{ opacity: 0, scale: 0.96, y: 24 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="hero-panel-head">
              <span className="pill">Platform overview</span>
              <span className="muted">Dark workspace</span>
            </div>
            <div className="hero-summary-card">
              <span className="card-kicker">Designed for focused review</span>
              <strong>Minimal structure, live data, clear outputs.</strong>
              <p>Search the field you want, inspect the market, and keep resume outputs tied to the selected role.</p>
            </div>
            <div className="hero-list">
              {platformHighlights.map((item) => (
                <div className="hero-list-item" key={item}>
                  <span className="hero-list-dot" />
                  <p>{item}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </section>

        <motion.section className="metrics-grid" initial="hidden" whileInView="show" viewport={{ once: true }} variants={sectionStagger}>
          {metricItems.map((item, index) => (
            <motion.div className="metric-card" key={item.label} variants={fadeUp} custom={index * 0.04}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </motion.div>
          ))}
        </motion.section>

        <motion.section className="content-section" id="features" initial="hidden" whileInView="show" viewport={{ once: true }} variants={sectionStagger}>
          <motion.div className="section-heading" variants={fadeUp}>
            <p className="eyebrow">Feature architecture</p>
            <h2>Core features, grouped properly.</h2>
          </motion.div>
          <div className="feature-grid">
            {featureCards.map((feature, index) => (
              <motion.article className="feature-card" key={feature.title} variants={fadeUp} custom={index * 0.06}>
                <div className="feature-index">0{index + 1}</div>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </motion.article>
            ))}
          </div>
        </motion.section>

        <motion.section className="content-section workflow-panel" id="workflow" initial="hidden" whileInView="show" viewport={{ once: true }} variants={sectionStagger}>
          <motion.div className="section-heading narrow" variants={fadeUp}>
            <p className="eyebrow">How it moves</p>
            <h2>A direct workflow from search to output.</h2>
          </motion.div>
          <div className="timeline-grid">
            {workflowSteps.map((step, index) => (
              <motion.div className="timeline-card" key={step} variants={fadeUp} custom={index * 0.05}>
                <span>{index + 1}</span>
                <p>{step}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.section className="content-section dual-panel" initial="hidden" whileInView="show" viewport={{ once: true }} variants={sectionStagger}>
          <motion.div className="section-heading" variants={fadeUp}>
            <p className="eyebrow">Market overview</p>
            <h2>Live source coverage at a glance.</h2>
            <p className="section-copy">
              The landing page should explain the product and show current market coverage without visual overload.
            </p>
          </motion.div>
          <motion.div className="detail-card" variants={fadeUp} custom={0.08}>
            {sourceHighlights.length ? (
              sourceHighlights.map((source) => (
                <div className="detail-row" key={source.source_key}>
                  <span>{source.source_key}</span>
                  <strong>{source.status === "ok" ? `${source.jobs_found} jobs` : source.status}</strong>
                </div>
              ))
            ) : (
              <>
                <div className="detail-row">
                  <span>Field search entrypoint</span>
                  <strong>Hero + dashboard</strong>
                </div>
                <div className="detail-row">
                  <span>Resume behavior</span>
                  <strong>Dynamic</strong>
                </div>
                <div className="detail-row">
                  <span>Cover letter behavior</span>
                  <strong>Role-specific</strong>
                </div>
                <div className="detail-row">
                  <span>Visual direction</span>
                  <strong>Professional dark workspace</strong>
                </div>
              </>
            )}
          </motion.div>
        </motion.section>
      </main>
    </Shell>
  );
}

function StatusBanner({ error, success }) {
  if (!error && !success) return null;
  return <div className={`status-banner ${error ? "error" : "success"}`}>{error || success}</div>;
}

function getPlainDescription(description, limit = 280) {
  if (!description) return "No description available yet.";
  return description.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, limit);
}

function DashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [fieldInput, setFieldInput] = useState(searchParams.get("field") || "");
  const [jobsData, setJobsData] = useState({ jobs: [], total: 0 });
  const [stats, setStats] = useState(null);
  const [profile, setProfile] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [artifactsByJob, setArtifactsByJob] = useState({});
  const [activeOutput, setActiveOutput] = useState("summary");
  const [status, setStatus] = useState({ error: "", success: "" });
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [tailoring, setTailoring] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sourceData, setSourceData] = useState(null);
  const [notificationPermission, setNotificationPermission] = useState(
    typeof window !== "undefined" && "Notification" in window ? Notification.permission : "unsupported"
  );
  const [lastAutoCheck, setLastAutoCheck] = useState("");
  const [liveMonitoring, setLiveMonitoring] = useState(true);
  const scrapingRef = useRef(false);

  async function loadBaseState(query = fieldInput) {
    setLoadingJobs(true);
    try {
      const field = query.trim();
      const jobsUrl = field ? `/api/scraped-jobs?search=${encodeURIComponent(field)}&limit=24` : "/api/scraped-jobs?limit=24";
      const [jobsResponse, statsResponse, profileResponse, sourcesResponse] = await Promise.all([
        fetchJson(jobsUrl),
        fetchJson("/api/stats"),
        fetchJson("/api/profile"),
        fetchJson("/api/sources")
      ]);
      setJobsData(jobsResponse);
      setStats(statsResponse.stats);
      setProfile(profileResponse.profile);
      setSourceData(sourcesResponse);
      if (jobsResponse.jobs?.length) {
        setSelectedJobId((current) => current || jobsResponse.jobs[0].id);
      }
    } catch (error) {
      setStatus({ error: error.message, success: "" });
    } finally {
      setLoadingJobs(false);
    }
  }

  useEffect(() => {
    loadBaseState(searchParams.get("field") || "");
  }, []);

  useEffect(() => {
    const nextField = searchParams.get("field") || "";
    setFieldInput(nextField);
  }, [searchParams]);

  useEffect(() => {
    if (typeof window === "undefined" || !("Notification" in window)) {
      setNotificationPermission("unsupported");
      return;
    }

    setNotificationPermission(Notification.permission);
    if (Notification.permission === "default") {
      Notification.requestPermission()
        .then((permission) => {
          setNotificationPermission(permission);
        })
        .catch(() => {});
    }
  }, []);

  const selectedJob = useMemo(
    () => jobsData.jobs.find((job) => job.id === selectedJobId) || jobsData.jobs[0] || null,
    [jobsData.jobs, selectedJobId]
  );
  const artifact = selectedJob ? artifactsByJob[selectedJob.id] || null : null;

  const dashboardSummary = [
    { label: "Jobs", value: formatNumber(stats?.jobs_scraped ?? jobsData.total ?? 0) },
    { label: "Search results", value: formatNumber(jobsData.jobs.length) },
    { label: "Strong matches", value: formatNumber(stats?.strong_matches ?? 0) },
    { label: "Profile", value: profile ? "Ready" : "Missing" }
  ];
  const marketSources = (sourceData?.last_scrape?.sources || []).slice(0, 6);

  useEffect(() => {
    scrapingRef.current = scraping;
  }, [scraping]);

  useEffect(() => {
    if (!selectedJob?.id || !profile) {
      return;
    }
    if (artifactsByJob[selectedJob.id]) {
      return;
    }

    let cancelled = false;
    setTailoring(true);
    setStatus({ error: "", success: "" });

    fetchJson(`/api/jobs/${selectedJob.id}/tailor`, { method: "POST" })
      .then((data) => {
        if (!cancelled) {
          setArtifactsByJob((current) => ({ ...current, [selectedJob.id]: data.artifact }));
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setStatus({ error: error.message, success: "" });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setTailoring(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedJob?.id, profile?.updated_at, artifactsByJob]);

  async function handleSearch(event) {
    event.preventDefault();
    const nextField = fieldInput.trim();
    setSearchParams(nextField ? { field: nextField } : {});
    await loadBaseState(nextField);
  }

  async function handleScrape() {
    setScraping(true);
    scrapingRef.current = true;
    setStatus({ error: "", success: "" });
    try {
      const response = await fetchJson("/api/scrape", { method: "POST" });
      await loadBaseState(fieldInput);
      setStatus({
        error: "",
        success: `Scrape completed. ${response.total_jobs} jobs available, ${response.new_jobs} newly added.`
      });
    } catch (error) {
      setStatus({ error: error.message, success: "" });
    } finally {
      setScraping(false);
      scrapingRef.current = false;
    }
  }

  useEffect(() => {
    if (!liveMonitoring) return undefined;

    let cancelled = false;

    async function runAutoScrape() {
      if (scrapingRef.current) return;
      scrapingRef.current = true;
      setScraping(true);
      try {
        const response = await fetchJson("/api/scrape", { method: "POST" });
        if (cancelled) return;
        await loadBaseState(fieldInput);
        const checkedAt = new Date().toISOString();
        setLastAutoCheck(checkedAt);
        if (response.new_jobs > 0) {
          const message = `${response.new_jobs} new jobs found. Total jobs: ${response.total_jobs}.`;
          setStatus({ error: "", success: `Live monitoring update: ${message}` });
          playNotificationTone();
          sendBrowserNotification("JobIntel live scrape", message);
        }
      } catch (error) {
        if (!cancelled) {
          setStatus({ error: `Live monitoring failed: ${error.message}`, success: "" });
          setLastAutoCheck(new Date().toISOString());
        }
      } finally {
        scrapingRef.current = false;
        if (!cancelled) {
          setScraping(false);
        }
      }
    }

    const timer = window.setInterval(runAutoScrape, AUTO_SCRAPE_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [fieldInput, liveMonitoring]);

  async function handleResumeUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setStatus({ error: "", success: "" });
    try {
      const formData = new FormData();
      formData.append("resume", file);
      const response = await fetchJson("/api/profile/upload", { method: "POST", body: formData });
      setProfile(response.profile);
      setArtifactsByJob({});
      setStatus({
        error: "",
        success: `Resume profile updated from ${response.profile?.source_filename || file.name}. Tailored content is now dynamic.`
      });
      await loadBaseState(fieldInput);
    } catch (error) {
      setStatus({ error: error.message, success: "" });
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleEnableAlerts() {
    try {
      const permission = await requestNotificationAccess();
      setNotificationPermission(permission);
      if (permission === "granted") {
        playNotificationTone();
        sendBrowserNotification("JobIntel alerts enabled", "You will now receive alerts when new jobs are found.");
        setStatus({ error: "", success: "Alerts enabled. Browser notifications and sound are now active." });
      } else {
        setStatus({ error: "Notification permission was not granted.", success: "" });
      }
    } catch (error) {
      setStatus({ error: `Unable to enable alerts: ${error.message}`, success: "" });
    }
  }

  function handleTestAlert() {
    playNotificationTone();
    sendBrowserNotification("JobIntel test alert", "This is a test notification from the live scraping monitor.");
    setStatus({ error: "", success: "Test alert sent. If you did not hear a sound or see a notification, the browser blocked it." });
  }

  function handleJobAction(jobId, outputType) {
    setSelectedJobId(jobId);
    setActiveOutput(outputType);
  }

  const outputActions = [
    { key: "summary", label: "Summary", short: "SUM" },
    { key: "cover", label: "Cover", short: "CL" },
    { key: "resume", label: "Resume PDF", short: "PDF" }
  ];

  return (
    <Shell>
      <main className="dashboard-page">
        <motion.section
          className="dashboard-hero"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        >
          <div>
            <p className="eyebrow">Application workspace</p>
            <h1>Search, review, and generate.</h1>
            <p className="section-copy">
              A cleaner workspace with dedicated sections for search, jobs, selected role detail, and generated outputs.
            </p>
          </div>
          <div className="dashboard-actions">
            <button className="button button-primary" onClick={handleScrape} disabled={scraping}>
              {scraping ? "Refreshing jobs..." : "Run live scrape"}
            </button>
            <label className="button button-secondary upload-button">
              {uploading ? "Uploading..." : "Upload resume"}
              <input type="file" accept=".pdf,.doc,.docx,.txt,.md,.html,.htm" onChange={handleResumeUpload} hidden />
            </label>
          </div>
        </motion.section>

        <StatusBanner error={status.error} success={status.success} />

        <section className="dashboard-summary-strip">
          {dashboardSummary.map((item) => (
            <div className="summary-box" key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </section>

        <section className="workspace-top-grid">
          <div className="workspace-column">
            <div className="panel glass">
              <div className="section-tag" id="search-section">
                Search & profile
              </div>
              <div className="panel-head">
                <h2>Search</h2>
                <span>{loadingJobs ? "Loading..." : `${jobsData.total || 0} roles`}</span>
              </div>
              <form className="toolbar-form" onSubmit={handleSearch}>
                <input
                  value={fieldInput}
                  onChange={(event) => setFieldInput(event.target.value)}
                  placeholder="Search by field, title, stack, or keyword"
                />
                <button className="button button-primary" type="submit">
                  Search
                </button>
              </form>
              <div className="metric-strip">
                <div>
                  <span>Jobs scraped</span>
                  <strong>{formatNumber(stats?.jobs_scraped ?? jobsData.total ?? 0)}</strong>
                </div>
                <div>
                  <span>Strong matches</span>
                  <strong>{formatNumber(stats?.strong_matches ?? 0)}</strong>
                </div>
                <div>
                  <span>Profile</span>
                  <strong>{profile ? "Loaded" : "Missing"}</strong>
                </div>
              </div>
            </div>
          </div>

          <div className="panel market-panel" id="market-section">
              <div className="section-tag">Market & source status</div>
              <div className="panel-head">
                <h2>Market</h2>
                <span>{sourceData?.last_scrape?.last_scrape ? "Latest scrape" : "No scrape data"}</span>
              </div>
              <div className="monitor-panel">
                <div className="monitor-row">
                  <span>Live scraping</span>
                  <strong>{liveMonitoring ? "Running" : "Paused"}</strong>
                </div>
                <div className="monitor-row">
                  <span>Notifications</span>
                  <strong>{notificationPermission}</strong>
                </div>
                <div className="monitor-row">
                  <span>Last check</span>
                  <strong>{formatTime(lastAutoCheck)}</strong>
                </div>
                <div className="monitor-actions">
                  <button className="button button-secondary monitor-toggle" type="button" onClick={() => setLiveMonitoring((value) => !value)}>
                    {liveMonitoring ? "Pause monitoring" : "Resume monitoring"}
                  </button>
                  <button className="button button-secondary monitor-toggle" type="button" onClick={handleEnableAlerts}>
                    Enable alerts
                  </button>
                  <button className="button button-secondary monitor-toggle" type="button" onClick={handleTestAlert}>
                    Test alert
                  </button>
                </div>
              </div>
              <div className="source-list">
                {marketSources.map((source) => (
                  <div className="source-row" key={source.source_key}>
                    <div>
                      <strong>{source.source_key}</strong>
                      <span>{source.elapsed_seconds}s</span>
                    </div>
                    <div className={`source-badge ${source.status}`}>
                      {source.status === "ok" ? `${source.jobs_found} jobs` : source.status}
                    </div>
                  </div>
                ))}
                {!marketSources.length && <div className="empty-state">Run a scrape to see source coverage and timing.</div>}
              </div>
          </div>
        </section>

        <section className="panel jobs-board-panel" id="jobs-section">
          <div className="section-tag">Job results</div>
          <div className="panel-head">
            <h2>Jobs</h2>
            <span>{jobsData.jobs.length} shown</span>
          </div>
          <div className="jobs-board">
            <AnimatePresence>
              {jobsData.jobs.map((job, index) => {
                const isActive = selectedJob?.id === job.id;
                const hasArtifact = Boolean(artifactsByJob[job.id]);
                return (
                  <motion.article
                    key={job.id}
                    className={`job-card board-card ${isActive ? "active" : ""}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.35, delay: index * 0.02 }}
                  >
                    <button className="job-card-main" type="button" onClick={() => setSelectedJobId(job.id)}>
                      <div className="job-card-top">
                        <span className="job-source">{job.source}</span>
                        <span className="job-match">{job.match?.score ? `${job.match.score}% match` : "Review"}</span>
                      </div>
                      <strong>{job.title}</strong>
                      <p>{job.company}</p>
                      <div className="job-meta">
                        <span>{job.location}</span>
                        <span>{job.remote_policy}</span>
                        <span>{job.salary}</span>
                      </div>
                      <p className="job-snippet">{getPlainDescription(job.description, 180)}</p>
                    </button>
                    <div className="job-card-footer">
                      <div className="job-output-actions" aria-label={`Generated outputs for ${job.title}`}>
                        {outputActions.map((action) => (
                          <button
                            key={action.key}
                            type="button"
                            className={`output-icon-button ${isActive && activeOutput === action.key ? "active" : ""}`}
                            title={action.label}
                            aria-label={action.label}
                            onClick={() => handleJobAction(job.id, action.key)}
                          >
                            <span>{action.short}</span>
                            <small>{action.label}</small>
                          </button>
                        ))}
                      </div>
                      <span className="job-output-state">{profile ? (hasArtifact ? "Outputs ready" : "Preparing outputs") : "Resume required"}</span>
                    </div>
                  </motion.article>
                );
              })}
            </AnimatePresence>
            {!jobsData.jobs.length && <div className="empty-state">No jobs matched this field yet. Try a broader search.</div>}
          </div>
        </section>

        <section className="workspace-bottom-grid">
          <div className="panel detail-hero">
            <div className="section-tag" id="detail-section">
              Selected role
            </div>
            <div className="panel-head">
              <h2>Job details</h2>
              <span>{selectedJob?.source || "No selection"}</span>
            </div>
            {selectedJob ? (
              <>
                <h3>{selectedJob.title}</h3>
                <p className="job-company">{selectedJob.company}</p>
                <div className="chip-row">
                  <span className="chip">{selectedJob.location}</span>
                  <span className="chip">{selectedJob.remote_policy}</span>
                  <span className="chip">{selectedJob.salary}</span>
                </div>
                <p className="job-description">{getPlainDescription(selectedJob.description, 520)}</p>
                <a className="button button-secondary" href={selectedJob.url} target="_blank" rel="noreferrer">
                  Open original job
                </a>
              </>
            ) : (
              <div className="empty-state">Pick a job to inspect its details.</div>
            )}
          </div>

          <div className="panel outputs-panel" id="outputs-section">
            <div className="section-tag">Generated outputs</div>
              <div className="panel-head">
                <h2>Output preview</h2>
                <span>{artifact?.match?.score ? `${artifact.match.score}% match` : "Awaiting profile"}</span>
              </div>
              {!profile && (
                <div className="resume-required-banner" role="alert" aria-live="polite">
                  <strong>Warning: resume required</strong>
                  <p>Upload a resume first to generate the summary, tailored cover letter, and match evidence for the selected job.</p>
                </div>
              )}
              <div className="output-tab-row" role="tablist" aria-label="Output type">
                {outputActions.map((action) => (
                  <button
                    key={action.key}
                    type="button"
                    className={`output-tab ${activeOutput === action.key ? "active" : ""}`}
                    onClick={() => setActiveOutput(action.key)}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
              <div className="panel preview-card output-preview-card">
                {activeOutput === "summary" && (
                  <>
                    <div className="panel-head">
                      <h3>Summary</h3>
                      <span className={!profile ? "state-alert" : ""}>{tailoring ? "Generating..." : profile ? "Live" : "Needs resume"}</span>
                    </div>
                    <p>
                      {artifact?.resume?.summary ||
                        profile?.summary ||
                        "Upload a resume to generate a job-aware summary that updates with the selected role."}
                    </p>
                  </>
                )}
                {activeOutput === "cover" && (
                  <>
                    <div className="panel-head">
                      <h3>Cover letter</h3>
                      <span className={!profile ? "state-alert" : ""}>
                        {profile ? `${artifact?.packet_validation?.score || artifact?.validation?.score || "--"} score` : "Needs resume"}
                      </span>
                    </div>
                    <p>
                      {artifact?.cover_letter?.text?.slice(0, 720) ||
                        "Once a resume is loaded, the selected job will generate a tailored cover letter preview here."}
                    </p>
                    {artifact?.cover_letter?.pdf_url && (
                      <a className="button button-secondary" href={artifact.cover_letter.pdf_url} target="_blank" rel="noreferrer">
                        Open cover letter PDF
                      </a>
                    )}
                  </>
                )}
                {activeOutput === "resume" && (
                  <>
                    <div className="panel-head">
                      <h3>Tailored resume PDF</h3>
                      <span className={!profile ? "state-alert" : ""}>
                        {profile ? `${artifact?.overall_validation?.resume_score || artifact?.validation?.score || "--"} score` : "Needs resume"}
                      </span>
                    </div>
                    <p>
                      {artifact?.resume?.headline
                        ? `${artifact.resume.headline}. ${artifact.resume.summary || ""}`
                        : "Upload a resume to generate a tailored resume file for the selected role."}
                    </p>
                    <div className="preview-file-meta">
                      <strong>Status</strong>
                      <span>{artifact?.pdf_filename || "No PDF generated yet"}</span>
                    </div>
                    {artifact?.download_url && (
                      <a className="button button-primary" href={artifact.download_url} target="_blank" rel="noreferrer">
                        Open tailored resume PDF
                      </a>
                    )}
                  </>
                )}
              </div>
              <div className="evidence-grid">
                <div className="evidence-card">
                  <h3>Matched keywords</h3>
                  <div className="chip-row">
                    {(artifact?.validation?.matched_keywords || artifact?.match?.matched_keywords || []).slice(0, 8).map((item) => (
                      <span className="chip" key={item}>
                        {item}
                      </span>
                    ))}
                    {!artifact && <span className="muted-block">Load a resume to see matched evidence.</span>}
                  </div>
                </div>
                <div className="evidence-card">
                  <h3>Resume headline</h3>
                  <p>{artifact?.resume?.headline || profile?.headline || "No active profile headline yet."}</p>
                </div>
                <div className="evidence-card">
                  <h3>Tailored experience</h3>
                  <ul className="bullet-list">
                    {(artifact?.resume?.experience || profile?.skills || []).slice(0, 4).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div className="evidence-card">
                  <h3>Packet validation</h3>
                  <ul className="bullet-list">
                    {(artifact?.packet_validation?.issues || artifact?.validation?.issues || []).slice(0, 4).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                    {!artifact && <li>The validation layer activates when both a resume and job are present.</li>}
                  </ul>
                </div>
              </div>
          </div>
        </section>
      </main>
    </Shell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
    </Routes>
  );
}
