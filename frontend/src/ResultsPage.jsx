
function ResultsPage() {
    const { submissionId } = useParams()
    const { user } = useAuth()
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [activeTab, setActiveTab] = useState('summary')

    useEffect(() => {
        loadResults()
    }, [submissionId])

    const loadResults = async () => {
        try {
            const res = await api.get(`/results/submission/${submissionId}`)
            setResult(res.data)
        } catch (err) {
            setError('Failed to load results')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="loading"><span className="spinner"></span> Loading Results...</div>
    if (error) return <div className="alert alert-error">{error}</div>
    if (!result) return <div className="alert alert-info">No results found</div>

    const { submission, total_result, answers } = result
    const statusClass = `badge badge-${submission.status}`
    const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

    const handleFinalize = async () => {
        if (!confirm('Are you sure you want to finalize this review?')) return
        try {
            await api.post(`/results/submission/${submissionId}/finalize`)
            loadResults()
        } catch (err) {
            alert('Failed to finalize')
        }
    }

    const handlePublish = async () => {
        try {
            await api.post(`/results/submission/${submissionId}/publish`)
            loadResults()
        } catch (err) {
            alert('Failed to publish')
        }
    }

    const handleDownload = async () => {
        try {
            const response = await api.get(`/results/submission/${submissionId}/download`, {
                responseType: 'blob'
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `report_${submissionId}.pdf`)
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (err) {
            alert('Failed to download report')
        }
    }

    return (
        <div className="results-page container">
            <div className="results-header">
                <div>
                    <h1>Evaluation Report</h1>
                    <p className="text-muted">Exam: {submission.exam_id} • Student: {submission.student_id}</p>
                </div>
                <div className="results-actions">
                    {isTeacher && (
                        <>
                            {submission.status !== 'completed' && (
                                <button className="btn btn-primary" onClick={handleFinalize}>✅ Finalize Review</button>
                            )}
                            {submission.status === 'completed' && !result.is_published && (
                                <button className="btn btn-primary" onClick={handlePublish}>📢 Publish Results</button>
                            )}
                        </>
                    )}
                    <button className="btn btn-outline-primary" onClick={handleDownload}>📥 Download PDF</button>
                    <button className="btn btn-secondary" onClick={() => window.print()}>🖨️ Print</button>
                    <Link to="/submissions" className="btn btn-outline">Back</Link>
                </div>
            </div>

            <div className="score-card card">
                <div className="score-circle" style={{
                    background: `conic-gradient(var(--primary-color) ${total_result.percentage}%, #e2e8f0 0)`
                }}>
                    <div className="score-inner">
                        <span className="score-grade">{total_result.grade}</span>
                        <span className="score-percent">{total_result.percentage.toFixed(1)}%</span>
                    </div>
                </div>
                <div className="score-details">
                    <div className="score-item">
                        <span className="label">Total Score</span>
                        <span className="value">{total_result.total_marks} / {total_result.max_marks}</span>
                    </div>
                    <div className="score-item">
                        <span className="label">Status</span>
                        <span className={`value ${statusClass}`}>{submission.status}</span>
                    </div>
                    <div className="score-item">
                        <span className="label">Evaluated At</span>
                        <span className="value">{new Date(total_result.created_at).toLocaleString()}</span>
                    </div>
                </div>
            </div>

            <div className="results-tabs">
                <button
                    className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('summary')}
                >
                    Question Breakdown
                </button>
                <button
                    className={`tab ${activeTab === 'extracted' ? 'active' : ''}`}
                    onClick={() => setActiveTab('extracted')}
                >
                    Extracted Text
                </button>
            </div>

            {activeTab === 'summary' ? (
                <div className="questions-list">
                    {answers.map((ans, idx) => (
                        <QuestionCard
                            key={idx}
                            ans={ans}
                            submissionId={submissionId}
                            isTeacher={isTeacher}
                            onUpdate={loadResults}
                        />
                    ))}
                </div>
            ) : (
                <div className="extracted-text card">
                    <pre>{JSON.stringify(answers, null, 2)}</pre>
                </div>
            )}
        </div>
    )
}

function QuestionCard({ ans, submissionId, isTeacher, onUpdate }) {
    const [editing, setEditing] = useState(false)
    const [marks, setMarks] = useState(ans.marks_obtained)
    const [feedback, setFeedback] = useState(ans.feedback || '')

    const handleSave = async () => {
        try {
            await api.put(`/results/submission/${submissionId}/question/${ans.question_no}`, {
                marks_obtained: parseFloat(marks),
                feedback: feedback
            })
            setEditing(false)
            onUpdate()
        } catch (err) {
            alert('Failed to save: ' + (err.response?.data?.detail || err.message))
        }
    }

    if (editing) {
        return (
            <div className="question-card card editing">
                <div className="q-header">
                    <h3>Question {ans.question_no}</h3>
                    <div className="q-actions">
                        <button className="btn btn-sm btn-primary" onClick={handleSave}>Save</button>
                        <button className="btn btn-sm btn-outline" onClick={() => setEditing(false)}>Cancel</button>
                    </div>
                </div>
                <div className="form-group">
                    <label>Marks (Max: {ans.max_marks})</label>
                    <input
                        type="number"
                        step="0.5"
                        max={ans.max_marks}
                        className="form-input"
                        value={marks}
                        onChange={(e) => setMarks(e.target.value)}
                    />
                </div>
                <div className="form-group">
                    <label>Feedback</label>
                    <textarea
                        className="form-input"
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                    />
                </div>
            </div>
        )
    }

    return (
        <div className={`question-card card ${ans.marks_obtained === ans.max_marks ? 'perfect' : ''}`}>
            <div className="q-header">
                <h3>Question {ans.question_no}</h3>
                <div className="q-actions">
                    <span className="q-score">
                        {ans.marks_obtained} / {ans.max_marks}
                    </span>
                    {isTeacher && (
                        <button className="btn btn-sm btn-secondary" onClick={() => setEditing(true)}>✏️ Edit</button>
                    )}
                </div>
            </div>

            <div className="q-feedback">
                <div className="feedback-section">
                    <strong>Keyword Match:</strong>
                    <p>{ans.keywords_matched ? ans.keywords_matched.join(', ') : <span className="text-muted">No keywords matched</span>}</p>
                </div>
                {ans.feedback && (
                    <div className="feedback-section">
                        <strong>Feedback:</strong>
                        <p>{ans.feedback}</p>
                    </div>
                )}
            </div>
        </div>
    )
}
