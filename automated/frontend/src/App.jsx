import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Routes, Route, Navigate, Link, useNavigate, useParams } from 'react-router-dom'
import api from './api'
import { AuthContext, useAuth } from './AuthContext'
import './App.css'
import ExamsPage from './ExamsPage'
import { SplineScene } from './components/ui/SplineScene.jsx'
import { GlowingEffect } from './components/ui/GlowingEffect.jsx'
import { Upload, Bot, Zap, ShieldCheck, BarChart2 } from 'lucide-react'


// ============ NAVBAR ============
function Navbar({ user, onLogout }) {
    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <Link to="/">
                    <span className="navbar-brand-icon">📝</span>
                    Automated Answer Sheet Evaluation
                </Link>
            </div>
            <div className="navbar-menu">
                {user ? (
                    <>
                        <Link to="/dashboard">Dashboard</Link>
                        {user.role === 'student' && (
                            <Link to="/results-view">View Results</Link>
                        )}
                        {(user.role === 'teacher' || user.role === 'admin') && (
                            <>
                                <Link to="/exams">Exams</Link>
                                <Link to="/reviews">Reviews</Link>
                            </>
                        )}
                        <button className="btn-logout" onClick={onLogout}>Logout</button>
                    </>
                ) : (
                    <>
                        <Link to="/dashboard">Dashboard</Link>
                        <Link to="/login">
                            <button className="navbar-btn navbar-btn-outline">Login</button>
                        </Link>
                        <Link to="/register">
                            <button className="navbar-btn navbar-btn-filled">Sign Up</button>
                        </Link>
                    </>
                )}
            </div>
        </nav>
    )
}

// ============ HOME PAGE ============
function HomePage() {
    const navigate = useNavigate()

    return (
        <div>
            {/* Hero Section */}
            <section className="hero">
                <div className="hero-inner">
                    <div className="hero-text">
                        <h1>Automated Answer Sheet Evaluation System</h1>
                        <p>Effortlessly Evaluate Student Exams with AI-Powered Accuracy</p>
                        <div className="hero-buttons">
                            <button className="btn-teacher" onClick={() => navigate('/login', { state: { role: 'teacher' } })}>
                                Teacher Login &rsaquo;
                            </button>
                            <button className="btn-student" onClick={() => navigate('/login', { state: { role: 'student' } })}>
                                Student Login &rsaquo;
                            </button>
                        </div>
                    </div>
                </div>
            </section>


            {/* Features Section — GlowingEffect Cards */}
            <section style={{ background: '#f8f9fa' }}>
                <h2 className="glowing-section-heading">How It Works</h2>
                <p className="glowing-section-sub">Hover over each card to see the rainbow glow effect</p>
                <ul className="glowing-grid">
                    {/* Card 1 */}
                    <li className="glowing-grid-item glowing-grid-item-1">
                        <div className="glowing-card-outer">
                            <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                            <div className="glowing-card-inner">
                                <div>
                                    <div className="glowing-card-icon-wrap"><Upload size={16} /></div>
                                </div>
                                <div>
                                    <h3 className="glowing-card-title">Upload Answer Sheets</h3>
                                    <p className="glowing-card-desc">Students submit PDF or image answer sheets directly from their device. Supports multiple formats including JPG, PNG, and PPT.</p>
                                </div>
                            </div>
                        </div>
                    </li>

                    {/* Card 2 */}
                    <li className="glowing-grid-item glowing-grid-item-2">
                        <div className="glowing-card-outer">
                            <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                            <div className="glowing-card-inner">
                                <div>
                                    <div className="glowing-card-icon-wrap"><Bot size={16} /></div>
                                </div>
                                <div>
                                    <h3 className="glowing-card-title">AI-Powered Evaluation</h3>
                                    <p className="glowing-card-desc">Groq's Llama 3.3 70B LLM semantically evaluates answers against the model key — far beyond simple keyword matching.</p>
                                </div>
                            </div>
                        </div>
                    </li>

                    {/* Card 3 — tall center card */}
                    <li className="glowing-grid-item glowing-grid-item-3">
                        <div className="glowing-card-outer">
                            <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                            <div className="glowing-card-inner">
                                <div>
                                    <div className="glowing-card-icon-wrap"><ShieldCheck size={16} /></div>
                                </div>
                                <div>
                                    <h3 className="glowing-card-title">Teacher Review Interface</h3>
                                    <p className="glowing-card-desc">Ambiguous answers are flagged for manual teacher review, ensuring no student is graded unfairly by the AI alone.</p>
                                </div>
                            </div>
                        </div>
                    </li>

                    {/* Card 4 */}
                    <li className="glowing-grid-item glowing-grid-item-4">
                        <div className="glowing-card-outer">
                            <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                            <div className="glowing-card-inner">
                                <div>
                                    <div className="glowing-card-icon-wrap"><Zap size={16} /></div>
                                </div>
                                <div>
                                    <h3 className="glowing-card-title">Instant Results</h3>
                                    <p className="glowing-card-desc">Get detailed marks, per-question feedback, and an overall grade the moment processing completes.</p>
                                </div>
                            </div>
                        </div>
                    </li>

                    {/* Card 5 — full width bottom */}
                    <li className="glowing-grid-item glowing-grid-item-5">
                        <div className="glowing-card-outer">
                            <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                            <div className="glowing-card-inner">
                                <div>
                                    <div className="glowing-card-icon-wrap"><BarChart2 size={16} /></div>
                                </div>
                                <div>
                                    <h3 className="glowing-card-title">Analytics & Reports</h3>
                                    <p className="glowing-card-desc">Track student performance trends over time. Teachers can view class-wide insights — pass rates, average scores, and flagged submissions — all from the dashboard.</p>
                                </div>
                            </div>
                        </div>
                    </li>
                </ul>
            </section>


            {/* About Section */}
            <section className="about-section">
                <div className="container">
                    <h2>About the System</h2>
                    <div className="about-divider"></div>
                    <div className="about-grid">
                        <div className="about-card">
                            <div className="about-icon-wrapper">📋</div>
                            <h3>Reduce Teacher Workload</h3>
                            <p>Students submit their answer sheets in PDF or image format.</p>
                        </div>
                        <div className="about-card">
                            <div className="about-icon-wrapper">🎯</div>
                            <h3>Accurate & Fast</h3>
                            <p>Our AI system compares answers to the model key and calculates scores.</p>
                        </div>
                        <div className="about-card">
                            <div className="about-icon-wrapper">⚖️</div>
                            <h3>Fair & Consistent</h3>
                            <p>Detailed marks and feedback instantly.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <p>© 2024 Automated Answer Sheet Evaluation System. All rights reserved.</p>
            </footer>
        </div>
    )
}

// ============ LOGIN PAGE ============
function LoginPage({ onLogin }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            const res = await api.post('/auth/login', { email, password })
            localStorage.setItem('access_token', res.data.access_token)
            localStorage.setItem('refresh_token', res.data.refresh_token)
            await onLogin()
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h2>Welcome Back</h2>
                <p>Sign in to your account</p>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input
                            type="email"
                            className="form-input"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={loading}>
                        {loading ? <span className="spinner"></span> : 'Sign In'}
                    </button>
                </form>

                <p className="auth-footer">
                    Don't have an account? <Link to="/register">Register</Link>
                </p>
            </div>
        </div>
    )
}

// ============ REGISTER PAGE ============
function RegisterPage({ onLogin }) {
    const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            await api.post('/auth/register', form)
            // Auto login after register
            const res = await api.post('/auth/login', { email: form.email, password: form.password })
            localStorage.setItem('access_token', res.data.access_token)
            await onLogin()
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <h2>Create Account</h2>
                <p>Get started with the evaluation system</p>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Full Name</label>
                        <input
                            type="text"
                            className="form-input"
                            value={form.name}
                            onChange={(e) => setForm({ ...form, name: e.target.value })}
                            placeholder="Your full name"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input
                            type="email"
                            className="form-input"
                            value={form.email}
                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                            placeholder="you@example.com"
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={form.password}
                            onChange={(e) => setForm({ ...form, password: e.target.value })}
                            placeholder="Min. 6 characters"
                            required
                            minLength={6}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Role</label>
                        <select
                            className="form-input"
                            value={form.role}
                            onChange={(e) => setForm({ ...form, role: e.target.value })}
                        >
                            <option value="student">Student</option>
                            <option value="teacher">Teacher</option>
                        </select>
                    </div>
                    <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={loading}>
                        {loading ? <span className="spinner"></span> : 'Create Account'}
                    </button>
                </form>

                <p className="auth-footer">
                    Already have an account? <Link to="/login">Sign in</Link>
                </p>
            </div>
        </div>
    )
}

// ============ TEACHER DASHBOARD ============
function TeacherDashboard({ user }) {
    const [stats, setStats] = useState({ totalStudents: 42, examsEvaluated: 12, sheetsEvaluated: 265 })
    const [recentEvals, setRecentEvals] = useState([
        { id: 6, date: 'April 22, 2024', marks: '85 / 100', status: 'Passed' },
        { id: 2, date: 'April 10, 2024', marks: '75 / 100', status: 'Passed' },
        { id: 1, date: 'April 15, 2024', marks: '44 / 100', status: 'Failed' },
    ])
    const navigate = useNavigate()

    // Try to load real data
    useEffect(() => {
        const loadData = async () => {
            try {
                const res = await api.get('/submissions/')
                if (res.data && res.data.length > 0) {
                    setStats(prev => ({
                        ...prev,
                        sheetsEvaluated: res.data.length
                    }))
                }
            } catch (err) {
                // Use default data
            }
        }
        loadData()
    }, [])

    return (
        <div className="dashboard">
            <div className="dashboard-welcome">
                <h1>Welcome, {user?.name} 👋</h1>
                <p>Here's your teacher dashboard overview</p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card glow-wrap">
                    <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                    <div className="stat-icon stat-icon-blue">👥</div>
                    <div className="stat-info">
                        <span className="stat-value">{stats.totalStudents}</span>
                        <span className="stat-label">Total Students</span>
                    </div>
                </div>
                <div className="stat-card glow-wrap">
                    <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                    <div className="stat-icon stat-icon-green">📝</div>
                    <div className="stat-info">
                        <span className="stat-value">{stats.examsEvaluated}</span>
                        <span className="stat-label">Exams Evaluated</span>
                    </div>
                </div>
                <div className="stat-card glow-wrap">
                    <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                    <div className="stat-icon stat-icon-purple">📊</div>
                    <div className="stat-info">
                        <span className="stat-value">{stats.sheetsEvaluated}</span>
                        <span className="stat-label">Answer Sheets Evaluated</span>
                    </div>
                </div>
            </div>

            {/* Upload & Recent Evaluations Side by Side */}
            <div className="dashboard-content">
                <div className="dashboard-section">
                    <h3>📤 Upload Question Paper & Key</h3>
                    <div className="upload-section-dashboard">
                        <span className="upload-icon-large">📄</span>
                        <p>Upload Question Paper & Key</p>
                        <button className="btn btn-primary" onClick={() => navigate('/exams/new')}>
                            Upload PDF &rsaquo;
                        </button>
                    </div>
                </div>

                <div className="dashboard-section">
                    <h3>📊 Recent Evaluations</h3>
                    <table className="eval-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Exam Date</th>
                                <th>Marks Scored</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recentEvals.map((item) => (
                                <tr key={item.id}>
                                    <td>{item.id}</td>
                                    <td>{item.date}</td>
                                    <td>{item.marks}</td>
                                    <td>
                                        <span className={`badge ${item.status === 'Passed' ? 'badge-passed' : 'badge-failed'}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <Link to="/submissions" className="view-all-link">View All Results &rsaquo;</Link>
                </div>
            </div>
        </div>
    )
}

// ============ STUDENT DASHBOARD ============
function StudentDashboard({ user }) {
    const [recentExams, setRecentExams] = useState([
        { name: 'Science Midterm', date: 'April 2, 2024', score: '76 / 100', status: 'Passed' },
        { name: 'Math Test', date: 'April 8, 2024', score: '86 / 100', status: 'Passed' },
        { name: 'History Quiz', date: 'April 10, 2024', score: '64 / 100', status: 'Passed' },
    ])
    const navigate = useNavigate()

    return (
        <div className="dashboard">
            <div className="dashboard-welcome">
                <h1>Welcome, {user?.name} 👋</h1>
                <p>Here's your recent activity</p>
            </div>

            {/* Action Cards */}
            <div className="student-actions">
                <div className="action-card glow-wrap">
                    <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                    <span className="action-card-icon">📤</span>
                    <h3>Upload Answer Sheet</h3>
                    <button className="btn btn-green" onClick={() => navigate('/submissions/new')}>
                        Upload Answer Sheet &rsaquo;
                    </button>
                </div>
                <div className="action-card glow-wrap">
                    <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                    <span className="action-card-icon">📊</span>
                    <h3>Check Evaluation Result</h3>
                    <button className="btn btn-primary" onClick={() => navigate('/submissions')}>
                        View Results &rsaquo;
                    </button>
                </div>
            </div>

            {/* Recent Exams Table */}
            <div className="recent-exams-section">
                <h3>Recent Exams</h3>
                <table className="eval-table">
                    <thead>
                        <tr>
                            <th>Exam</th>
                            <th>Date</th>
                            <th>Score</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recentExams.map((exam, idx) => (
                            <tr key={idx}>
                                <td>{exam.name}</td>
                                <td>{exam.date}</td>
                                <td>{exam.score}</td>
                                <td>
                                    <span className={`badge ${exam.status === 'Passed' ? 'badge-passed' : 'badge-failed'}`}>
                                        {exam.status}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

// ============ DASHBOARD ROUTER ============
function Dashboard({ user }) {
    if (user?.role === 'teacher' || user?.role === 'admin') {
        return <TeacherDashboard user={user} />
    }
    return <StudentDashboard user={user} />
}

// ============ SUBMISSIONS PAGE ============
function SubmissionsPage({ user }) {
    const [submissions, setSubmissions] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadSubmissions()
    }, [])

    const loadSubmissions = async () => {
        try {
            const res = await api.get('/submissions/')
            setSubmissions(res.data)
        } catch (err) {
            console.error('Error loading submissions:', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return <div className="loading"><span className="spinner"></span> Loading...</div>
    }

    return (
        <div className="submissions-page">
            <div className="page-header">
                <div>
                    <h1>My Submissions</h1>
                    <p className="text-muted">View all your submitted answer sheets</p>
                </div>
                <Link to="/submissions/new" className="btn btn-primary">+ New Submission</Link>
            </div>

            {submissions.length === 0 ? (
                <div className="empty-state">
                    <span className="empty-icon">📭</span>
                    <h3>No Submissions Yet</h3>
                    <p>Upload your first answer sheet to get started</p>
                    <Link to="/submissions/new" className="btn btn-primary">Upload Now</Link>
                </div>
            ) : (
                <div className="card glow-wrap">
                    <GlowingEffect spread={40} glow disabled={false} proximity={64} inactiveZone={0.01} borderWidth={3} />
                    <table className="eval-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>File</th>
                                <th>Status</th>
                                <th>Submitted</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {submissions.map(sub => (
                                <tr key={sub.id}>
                                    <td>#{sub.id}</td>
                                    <td>{sub.original_filename}</td>
                                    <td>
                                        <span className={`badge badge-${sub.status}`}>
                                            {sub.status}
                                        </span>
                                    </td>
                                    <td>{new Date(sub.submitted_at).toLocaleDateString()}</td>
                                    <td>
                                        <Link to={`/results/${sub.id}`} className="btn btn-primary btn-sm">
                                            View Results
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

// ============ UPLOAD PAGE ============
function UploadPage() {
    const [file, setFile] = useState(null)
    const [qpFile, setQpFile] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [message, setMessage] = useState({ text: '', type: '' })
    const navigate = useNavigate()

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile) setFile(droppedFile)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!file) {
            setMessage({ text: '❌ Please upload an answer sheet file.', type: 'error' })
            return
        }

        setUploading(true)
        setMessage({ text: '', type: '' })

        const formData = new FormData()
        formData.append('file', file)
        if (qpFile) formData.append('question_paper', qpFile)

        try {
            console.log('Sending direct upload request...');
            const res = await api.post('/submissions/direct-upload', formData);

            setMessage({ text: '✅ Upload successful! AI is evaluating your submission...', type: 'success' });

            const submissionId = res.data.id;
            // Navigate immediately — results page will poll until ready
            navigate(`/results/${submissionId}`);
        } catch (err) {
            console.error('Submit Error:', err);
            const errMsg = err.response?.data?.detail || err.message || 'Unknown error';
            const fullError = typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg);

            setMessage({ text: '❌ ' + fullError, type: 'error' });
        } finally {
            setUploading(false);
        }
    }

    return (
        <div className="upload-page">
            <h1>Upload Answer Sheet</h1>
            <p>Submit your answer sheet for AI-powered evaluation</p>

            {message.text && (
                <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                    {message.text}
                </div>
            )}

            <form onSubmit={handleSubmit} className="card" style={{ marginTop: '16px' }}>
                <div className="upload-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

                    {/* Answer Sheet Upload */}
                    <div className="upload-box-wrapper">
                        <label style={{ fontWeight: 600, marginBottom: '8px', display: 'block' }}>Student Answer Sheet</label>
                        <div
                            className={`file-upload ${dragOver ? 'dragover' : ''}`}
                            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                            onDragLeave={() => setDragOver(false)}
                            onDrop={handleDrop}
                            onClick={() => document.getElementById('file-input').click()}
                        >
                            <input
                                id="file-input"
                                type="file"
                                accept=".pdf,.png,.jpg,.jpeg,.tiff,.txt,.ppt,.pptx"
                                onChange={(e) => setFile(e.target.files[0])}
                                style={{ display: 'none' }}
                            />
                            {file ? (
                                <div className="file-preview">
                                    <span>📄</span>
                                    <p style={{ fontWeight: 600 }}>{file.name}</p>
                                    <small className="text-muted">
                                        {file.size > 1024 * 1024
                                            ? (file.size / (1024 * 1024)).toFixed(2) + ' MB'
                                            : (file.size / 1024).toFixed(2) + ' KB'}
                                    </small>
                                </div>
                            ) : (
                                <>
                                    <span className="upload-icon">📤</span>
                                    <p>Drop answer sheet or click</p>
                                    <small className="text-muted">PDF, PNG, JPG, PPT, TXT</small>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Question Paper Upload */}
                    <div className="upload-box-wrapper">
                        <label style={{ fontWeight: 600, marginBottom: '8px', display: 'block' }}>Question Paper (Optional)</label>
                        <div
                            className={`file-upload ${qpFile ? 'has-file' : ''}`}
                            onClick={() => document.getElementById('qp-input').click()}
                        >
                            <input
                                id="qp-input"
                                type="file"
                                accept=".pdf,.png,.jpg,.jpeg,.tiff"
                                onChange={(e) => setQpFile(e.target.files[0])}
                                style={{ display: 'none' }}
                            />
                            {qpFile ? (
                                <div className="file-preview">
                                    <span>📃</span>
                                    <p style={{ fontWeight: 600 }}>{qpFile.name}</p>
                                    <small className="text-muted">{(qpFile.size / 1024).toFixed(1)} KB</small>
                                </div>
                            ) : (
                                <>
                                    <span className="upload-icon">📑</span>
                                    <p>Upload Question Paper</p>
                                    <small className="text-muted">Optional reference for AI</small>
                                </>
                            )}
                        </div>
                    </div>

                </div>

                <button type="submit" className="btn btn-primary btn-block btn-lg" style={{ marginTop: '24px' }}>
                    {uploading ? <><span className="spinner"></span> Uploading & Processing...</> : 'Submit for Evaluation'}
                </button>
            </form>
        </div>
    )
}

// ============ RESULTS PAGE ============
function ResultsPage() {
    const { submissionId } = useParams()
    const [result, setResult] = useState(null)
    const [processing, setProcessing] = useState(false)
    const [processingStatus, setProcessingStatus] = useState('')
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [activeTab, setActiveTab] = useState('summary')
    const pollRef = useRef(null)

    useEffect(() => {
        loadResults()
        return () => {
            if (pollRef.current) clearInterval(pollRef.current)
        }
    }, [submissionId])

    const loadResults = async () => {
        try {
            const res = await api.get(`/results/submission/${submissionId}`)
            // 202 = still processing
            if (res.status === 202) {
                setProcessing(true)
                setProcessingStatus(res.data?.status || 'processing')
                setResult(null)
                // Start polling every 3 seconds
                if (!pollRef.current) {
                    pollRef.current = setInterval(async () => {
                        try {
                            const pollRes = await api.get(`/results/submission/${submissionId}`)
                            if (pollRes.status === 200) {
                                clearInterval(pollRef.current)
                                pollRef.current = null
                                setProcessing(false)
                                setResult(pollRes.data)
                            } else {
                                setProcessingStatus(pollRes.data?.status || 'processing')
                            }
                        } catch (pollErr) {
                            const status = pollErr.response?.status
                            // 422 = evaluation failed on backend
                            if (status === 422) {
                                clearInterval(pollRef.current)
                                pollRef.current = null
                                setProcessing(false)
                                setProcessingStatus('failed')
                            } else if (status !== 202 && status !== 404) {
                                clearInterval(pollRef.current)
                                pollRef.current = null
                                setProcessing(false)
                                setError(pollErr.response?.data?.detail || 'Evaluation failed')
                            }
                        }
                    }, 3000)
                }
            } else {
                setProcessing(false)
                setResult(res.data)
                if (pollRef.current) {
                    clearInterval(pollRef.current)
                    pollRef.current = null
                }
            }
        } catch (err) {
            const status = err.response?.status
            if (status === 404) {
                setError(err.response?.data?.detail || 'Submission not found')
            } else if (status === 202) {
                // axios may throw for 2xx non-200 depending on config
                setProcessing(true)
                setProcessingStatus('processing')
            } else if (status === 422) {
                // Evaluation failed on the backend
                setProcessing(false)
                setProcessingStatus('failed')
            } else {
                setError(err.response?.data?.detail || 'Failed to load results')
            }
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="loading"><span className="spinner"></span> Loading Results...</div>

    if (processing) {
        const isFailed = processingStatus === 'failed'
        return (
            <div className="results-page">
                <div className="processing-state" style={{ textAlign: 'center', padding: '60px 20px' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '16px' }}>{isFailed ? '❌' : '⚙️'}</div>
                    <h2 style={{ marginBottom: '8px' }}>
                        {isFailed ? 'Evaluation Failed' : 'AI is Evaluating Your Submission'}
                    </h2>
                    <p className="text-muted" style={{ marginBottom: '24px' }}>
                        {isFailed
                            ? 'The AI could not evaluate this file. This usually happens when the file has no readable text or is corrupted.'
                            : <>Status: <strong>{processingStatus}</strong> — This may take up to a minute. Results will appear automatically.</>}
                    </p>
                    {!isFailed && (
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginBottom: '24px' }}>
                            <span className="spinner"></span>
                            <span style={{ color: '#666' }}>Auto-refreshing every 3 seconds...</span>
                        </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginTop: '16px' }}>
                        {isFailed && (
                            <Link to="/submissions/new" className="btn btn-primary">
                                🔄 Try Again
                            </Link>
                        )}
                        <Link to="/submissions" className="btn btn-secondary">
                            ← Back to Submissions
                        </Link>
                    </div>
                </div>
            </div>
        )
    }

    if (error) return (
        <div className="results-page">
            <div className="alert alert-error">{error}</div>
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
                <button className="btn btn-primary" onClick={() => { setLoading(true); setError(''); loadResults(); }}>
                    🔄 Retry
                </button>
                <Link to="/submissions" className="btn btn-secondary" style={{ marginLeft: '12px' }}>
                    ← Back to Submissions
                </Link>
            </div>
        </div>
    )
    if (!result) return <div className="results-page"><div className="alert alert-info">No results found</div></div>

    // API returns: { submission_id, total_marks, max_marks, percentage, grade, ai_report_card, questions, is_published }
    const { submission_id, total_marks, max_marks, percentage, grade, ai_report_card, questions, is_published } = result

    return (
        <div className="results-page">
            <div className="results-header">
                <div>
                    <h1>Evaluation Report</h1>
                    <p className="text-muted">Submission #{submission_id}</p>
                </div>
                <div className="results-actions">
                    <button className="btn btn-secondary" onClick={() => window.print()}>🖨️ Print</button>
                    <Link to="/submissions" className="btn btn-primary">Back</Link>
                </div>
            </div>

            <div className="results-tabs">
                <button
                    className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('summary')}
                >
                    📊 Summary
                </button>
                <button
                    className={`tab-btn ${activeTab === 'questions' ? 'active' : ''}`}
                    onClick={() => setActiveTab('questions')}
                >
                    📝 Detailed Analysis
                </button>
                {ai_report_card && (
                    <button
                        className={`tab-btn ${activeTab === 'report' ? 'active' : ''}`}
                        onClick={() => setActiveTab('report')}
                    >
                        🎓 AI Report Card
                    </button>
                )}
            </div>

            {activeTab === 'summary' && (
                <div className="tab-content">
                    <div className="score-card">
                        <div className="score-circle" style={{
                            background: `conic-gradient(#3366cc ${percentage}%, #e9ecef 0)`
                        }}>
                            <div className="score-inner">
                                <span className="score-grade">{grade || '-'}</span>
                                <span className="score-percent">{percentage?.toFixed(1) || 0}%</span>
                            </div>
                        </div>
                        <div className="score-details">
                            <h3>Performance Overview</h3>
                            <div className="score-stats">
                                <div className="score-stat">
                                    <span className="label">Total Marks</span>
                                    <span className="value">{total_marks} / {max_marks}</span>
                                </div>
                                <div className="score-stat">
                                    <span className="label">Status</span>
                                    <span className={`value status-${grade === 'F' ? 'fail' : 'pass'}`}>
                                        {grade === 'F' ? 'Needs Improvement' : 'Success'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'report' && ai_report_card && (
                <div className="tab-content">
                    <div className="report-card-container card">
                        <div className="report-header">
                            <span className="report-icon">🎓</span>
                            <h2>Intelligent Academic Report Card</h2>
                        </div>
                        <div className="report-body markdown-body">
                            <ReactMarkdown>{ai_report_card}</ReactMarkdown>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'questions' && (
                <div className="tab-content">
                    <div className="questions-list">
                        {questions.map((q, idx) => (
                            <div key={idx} className="question-item card">
                                <div className="question-header">
                                    <h4>Question {q.question_no}</h4>
                                    <span className="marks-badge">{q.marks_obtained} / {q.max_marks}</span>
                                </div>
                                <div className="question-content">
                                    <p className="feedback-text">{q.feedback}</p>
                                    {q.keywords_matched && q.keywords_matched.length > 0 && (
                                        <div className="keywords-wrap">
                                            <small>Keywords matched:</small>
                                            <div className="tags">
                                                {q.keywords_matched.map((tag, i) => (
                                                    <span key={i} className="tag">{tag}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

// ============ REVIEW DASHBOARD ============
function ReviewDashboard() {
    const [submissions, setSubmissions] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadQueue()
    }, [])

    const loadQueue = async () => {
        try {
            const res = await api.get('/results/review-queue')
            setSubmissions(res.data)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="loading"><span className="spinner"></span> Loading Queue...</div>

    return (
        <div className="review-dashboard">
            <h1>📝 Review Queue</h1>
            <p className="text-muted">Submissions requiring manual grading</p>

            {submissions.length === 0 ? (
                <div className="empty-state" style={{ marginTop: '24px' }}>
                    <span className="empty-icon">🎉</span>
                    <h3>All Caught Up!</h3>
                    <p>No submissions pending review.</p>
                </div>
            ) : (
                <div className="queue-grid">
                    {submissions.map(sub => (
                        <div key={sub.submission_id} className="queue-card">
                            <div className="queue-info">
                                <h3>Submission #{sub.submission_id}</h3>
                                <p>Student ID: {sub.student_id}</p>
                                <small className="text-muted">Submitted: {new Date(sub.submitted_at).toLocaleDateString()}</small>
                            </div>
                            <Link to={`/results/${sub.submission_id}`} className="btn btn-primary" style={{ marginTop: '12px' }}>
                                Start Review
                            </Link>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

// ============ PROTECTED ROUTE ============
function ProtectedRoute({ children, user }) {
    if (!user) {
        return <Navigate to="/login" replace />
    }
    return children
}

// ============ MAIN APP ============
function App() {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        checkAuth()
    }, [])

    const checkAuth = async () => {
        const token = localStorage.getItem('access_token')
        if (token) {
            try {
                const res = await api.get('/auth/me')
                setUser(res.data)
            } catch {
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
            }
        }
        setLoading(false)
    }

    const handleLogout = () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setUser(null)
    }

    if (loading) {
        return (
            <div className="app-loading">
                <span className="spinner"></span>
                <p>Loading...</p>
            </div>
        )
    }

    return (
        <AuthContext.Provider value={{ user, setUser }}>
            <div className="app">
                <Navbar user={user} onLogout={handleLogout} />
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/login" element={<LoginPage onLogin={checkAuth} />} />
                        <Route path="/register" element={<RegisterPage onLogin={checkAuth} />} />
                        <Route path="/dashboard" element={
                            <ProtectedRoute user={user}><Dashboard user={user} /></ProtectedRoute>
                        } />
                        <Route path="/exams" element={
                            <ProtectedRoute user={user}><ExamsPage /></ProtectedRoute>
                        } />
                        <Route path="/submissions" element={
                            <ProtectedRoute user={user}><SubmissionsPage user={user} /></ProtectedRoute>
                        } />
                        <Route path="/submissions/new" element={
                            <ProtectedRoute user={user}><UploadPage /></ProtectedRoute>
                        } />
                        <Route path="/results/:submissionId" element={
                            <ProtectedRoute user={user}><ResultsPage /></ProtectedRoute>
                        } />
                        <Route path="/results-view" element={
                            <ProtectedRoute user={user}><SubmissionsPage user={user} /></ProtectedRoute>
                        } />
                        <Route path="/reviews" element={
                            <ProtectedRoute user={user}><ReviewDashboard /></ProtectedRoute>
                        } />
                    </Routes>
                </main>
            </div>
        </AuthContext.Provider>
    )
}

export default App

