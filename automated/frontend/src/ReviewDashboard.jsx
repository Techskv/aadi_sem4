
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
        <div className="review-dashboard container">
            <h1>📝 Review Queue</h1>
            <p className="text-muted">Submissions requiring manual grading</p>

            {submissions.length === 0 ? (
                <div className="empty-state card">
                    <span className="empty-icon">🎉</span>
                    <h3>All Caught Up!</h3>
                    <p>No submissions pending review.</p>
                </div>
            ) : (
                <div className="queue-grid">
                    {submissions.map(sub => (
                        <div key={sub.submission_id} className="queue-card card">
                            <div className="queue-info">
                                <h3>Submission #{sub.submission_id}</h3>
                                <p>Student ID: {sub.student_id}</p>
                                <small>Submitted: {new Date(sub.submitted_at).toLocaleDateString()}</small>
                            </div>
                            <Link to={`/results/${sub.submission_id}`} className="btn btn-primary">
                                Start Review
                            </Link>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
