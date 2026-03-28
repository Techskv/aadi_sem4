import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from './api'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'

export default function ExamsPage() {
    const [exams, setExams] = useState([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(null) // ID of exam being uploaded for
    const [message, setMessage] = useState({ text: '', type: '' })

    useEffect(() => {
        loadExams()
    }, [])

    const loadExams = async () => {
        try {
            const res = await api.get('/exams/')
            setExams(res.data)
        } catch (err) {
            console.error('Error loading exams:', err)
            setMessage({ text: 'Failed to load exams.', type: 'error' })
        } finally {
            setLoading(false)
        }
    }

    const handleFileUpload = async (examId, file) => {
        if (!file) return

        setUploading(examId)
        setMessage({ text: '', type: '' })

        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await api.post(`/exams/${examId}/reference-docs`, formData)
            setMessage({ 
                text: `✅ ${res.data.filename} indexed successfully!`, 
                type: 'success' 
            })
            // Refresh exams to show updated state if needed
            loadExams()
        } catch (err) {
            setMessage({ 
                text: `❌ Error: ${err.response?.data?.detail || 'Upload failed'}`, 
                type: 'error' 
            })
        } finally {
            setUploading(null)
        }
    }

    if (loading) return <div className="loading"><span className="spinner"></span> Loading Exams...</div>

    return (
        <div className="exams-page" style={{ padding: '20px' }}>
            <div className="page-header" style={{ marginBottom: '24px' }}>
                <h1>Manage Exams & RAG Context</h1>
                <p className="text-muted">Upload reference materials to improve AI evaluation accuracy.</p>
            </div>

            {message.text && (
                <div className={`alert alert-${message.type}`} style={{ marginBottom: '20px' }}>
                    {message.text}
                </div>
            )}

            <div className="exams-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
                {exams.map(exam => (
                    <div key={exam.id} className="card exam-card" style={{ padding: '20px', position: 'relative' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                                <h3 style={{ margin: 0 }}>{exam.name}</h3>
                                <span className="badge badge-primary">{exam.subject}</span>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <span className="text-muted" style={{ fontSize: '0.8rem' }}>{exam.total_marks} Marks</span>
                            </div>
                        </div>
                        
                        <p style={{ margin: '12px 0', fontSize: '0.9rem', color: '#666' }}>{exam.description}</p>

                        <div className="rag-section" style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #eee' }}>
                            <h4 style={{ fontSize: '0.9rem', marginBottom: '8px', display: 'flex', alignItems: 'center' }}>
                                <FileText size={14} style={{ marginRight: '6px' }} /> 
                                RAG Knowledge Base
                            </h4>
                            
                            <div className="upload-zone" style={{ position: 'relative' }}>
                                <input 
                                    type="file" 
                                    id={`file-${exam.id}`} 
                                    style={{ display: 'none' }} 
                                    onChange={(e) => handleFileUpload(exam.id, e.target.files[0])}
                                    accept=".pdf,.txt,.docx,.png,.jpg"
                                />
                                <button 
                                    className="btn btn-outline-primary btn-sm btn-block"
                                    onClick={() => document.getElementById(`file-${exam.id}`).click()}
                                    disabled={uploading === exam.id}
                                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}
                                >
                                    {uploading === exam.id ? (
                                        <><span className="spinner" style={{ width: '12px', height: '12px', marginRight: '8px' }}></span> Indexing...</>
                                    ) : (
                                        <><Upload size={14} style={{ marginRight: '8px' }} /> Upload Reference Content</>
                                    )}
                                </button>
                                <p style={{ fontSize: '0.75rem', color: '#888', marginTop: '6px', textAlign: 'center' }}>
                                    Upload textbooks, notes, or marking schemes.
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {exams.length === 0 && (
                <div className="empty-state">
                    <h3>No Exams Found</h3>
                    <p>Create an exam first or seed the database.</p>
                </div>
            )}
        </div>
    )
}
