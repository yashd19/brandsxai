import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  FileSearch, Upload, X, Plus, Download, Send, MessageSquare, 
  Loader2, CheckCircle, AlertCircle, FileText, Image, Trash2,
  History, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';
import './ClaimProcessing.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ClaimProcessing = () => {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [extractedCodes, setExtractedCodes] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [searchCode, setSearchCode] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showAddCode, setShowAddCode] = useState(false);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getToken = () => localStorage.getItem('token');

  // Fetch sessions
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Create new session
  const createNewSession = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ title: `Claim Session ${new Date().toLocaleDateString()}` })
      });
      
      if (res.ok) {
        const session = await res.json();
        setActiveSession(session);
        setMessages([]);
        setExtractedCodes([]);
        setUploadedFiles([]);
        fetchSessions();
        toast.success('New session created');
      }
    } catch (err) {
      toast.error('Failed to create session');
    } finally {
      setIsLoading(false);
    }
  };

  // Load session
  const loadSession = async (sessionId) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setActiveSession(data.session);
        setMessages(data.messages || []);
        setExtractedCodes(data.session?.extracted_codes || []);
        setShowHistory(false);
      }
    } catch (err) {
      toast.error('Failed to load session');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    const newFiles = [];
    
    for (const file of files) {
      const reader = new FileReader();
      await new Promise((resolve) => {
        reader.onload = () => {
          const base64 = reader.result.split(',')[1];
          newFiles.push({
            filename: file.name,
            content_type: file.type,
            base64_data: base64
          });
          resolve();
        };
        reader.readAsDataURL(file);
      });
    }
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  // Remove uploaded file
  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Send message
  const sendMessage = async () => {
    if (!inputMessage.trim() && uploadedFiles.length === 0) return;
    if (!activeSession) {
      toast.error('Please create or select a session first');
      return;
    }

    setIsSending(true);
    
    // Add user message to UI immediately
    const userMessage = {
      role: 'user',
      content: inputMessage || 'Extracting codes from uploaded documents...',
      file_info: uploadedFiles.map(f => ({ filename: f.filename, content_type: f.content_type }))
    };
    setMessages(prev => [...prev, userMessage]);
    
    const messageToSend = inputMessage;
    const filesToSend = [...uploadedFiles];
    setInputMessage('');
    setUploadedFiles([]);

    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions/${activeSession.id}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          content: messageToSend || 'Please extract ICD-10 codes from these documents.',
          file_data: filesToSend.length > 0 ? filesToSend : null
        })
      });

      if (res.ok) {
        const data = await res.json();
        
        // Add assistant response
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          codes_extracted: data.new_codes
        }]);
        
        // Update extracted codes
        setExtractedCodes(data.all_codes || []);
        
        if (data.new_codes?.length > 0) {
          toast.success(`Extracted ${data.new_codes.length} new code(s)`);
        }
      } else {
        toast.error('Failed to process message');
      }
    } catch (err) {
      toast.error('Error sending message');
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  // Remove code
  const removeCode = async (codeToRemove) => {
    const updatedCodes = extractedCodes.filter(c => c.code !== codeToRemove);
    
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions/${activeSession.id}/codes`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ codes: updatedCodes })
      });
      
      if (res.ok) {
        setExtractedCodes(updatedCodes);
        toast.success(`Removed ${codeToRemove}`);
      }
    } catch (err) {
      toast.error('Failed to remove code');
    }
  };

  // Search ICD-10 codes
  const searchICD10 = async (query) => {
    setSearchCode(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/icd10/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.codes || []);
      }
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  // Add code manually
  const addCode = async (code) => {
    if (extractedCodes.some(c => c.code === code.code)) {
      toast.error('Code already exists');
      return;
    }
    
    const updatedCodes = [...extractedCodes, { ...code, source_text: 'Manually added', confidence: 1.0 }];
    
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions/${activeSession.id}/codes`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ codes: updatedCodes })
      });
      
      if (res.ok) {
        setExtractedCodes(updatedCodes);
        setShowAddCode(false);
        setSearchCode('');
        setSearchResults([]);
        toast.success(`Added ${code.code}`);
      }
    } catch (err) {
      toast.error('Failed to add code');
    }
  };

  // Export to Excel
  const exportCodes = async () => {
    if (!activeSession || extractedCodes.length === 0) {
      toast.error('No codes to export');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/claim-processing/sessions/${activeSession.id}/export`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `icd10_codes_${activeSession.id.slice(0, 8)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        toast.success('Codes exported successfully');
      }
    } catch (err) {
      toast.error('Failed to export');
    }
  };

  return (
    <div className="claim-processing" data-testid="claim-processing-page">
      {/* Sidebar - Session History */}
      <div className={`cp-sidebar ${showHistory ? 'show' : ''}`}>
        <div className="cp-sidebar-header">
          <h3><History size={18} /> Session History</h3>
          <button className="cp-close-btn" onClick={() => setShowHistory(false)}>
            <X size={18} />
          </button>
        </div>
        <div className="cp-sessions-list">
          {sessions.map(session => (
            <div 
              key={session.id} 
              className={`cp-session-item ${activeSession?.id === session.id ? 'active' : ''}`}
              onClick={() => loadSession(session.id)}
              data-testid={`session-${session.id}`}
            >
              <FileText size={16} />
              <div className="cp-session-info">
                <span className="cp-session-title">{session.title}</span>
                <span className="cp-session-date">
                  {new Date(session.created_at).toLocaleDateString()}
                </span>
              </div>
              <span className="cp-session-codes">
                {(session.extracted_codes || []).length} codes
              </span>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="cp-no-sessions">No sessions yet</div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="cp-main">
        {/* Header */}
        <div className="cp-header">
          <div className="cp-header-left">
            <button 
              className="cp-history-btn" 
              onClick={() => setShowHistory(!showHistory)}
              data-testid="toggle-history-btn"
            >
              <History size={20} />
            </button>
            <h2>
              <FileSearch size={24} />
              ICD-10 Code Extractor
            </h2>
          </div>
          <div className="cp-header-actions">
            <button 
              className="cp-new-session-btn" 
              onClick={createNewSession}
              disabled={isLoading}
              data-testid="new-session-btn"
            >
              <Plus size={18} /> New Session
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="cp-content">
          {/* Chat Panel */}
          <div className="cp-chat-panel">
            {!activeSession ? (
              <div className="cp-welcome">
                <div className="cp-welcome-icon">
                  <FileSearch size={48} />
                </div>
                <h3>Medical Claims ICD-10 Extractor</h3>
                <p>Upload clinical notes (PDFs or images) and let AI extract ICD-10 codes automatically.</p>
                <button 
                  className="cp-start-btn" 
                  onClick={createNewSession}
                  disabled={isLoading}
                  data-testid="start-session-btn"
                >
                  {isLoading ? <Loader2 className="spin" size={20} /> : <Plus size={20} />}
                  Start New Session
                </button>
              </div>
            ) : (
              <>
                {/* Messages */}
                <div className="cp-messages" data-testid="messages-container">
                  {messages.length === 0 && (
                    <div className="cp-empty-chat">
                      <Upload size={32} />
                      <p>Upload a clinical note or ask a question to get started</p>
                    </div>
                  )}
                  
                  {messages.map((msg, idx) => (
                    <div key={idx} className={`cp-message ${msg.role}`}>
                      <div className="cp-message-content">
                        {msg.role === 'user' && msg.file_info?.length > 0 && (
                          <div className="cp-message-files">
                            {msg.file_info.map((f, i) => (
                              <span key={i} className="cp-file-badge">
                                {f.content_type?.includes('image') ? <Image size={14} /> : <FileText size={14} />}
                                {f.filename}
                              </span>
                            ))}
                          </div>
                        )}
                        <p>{msg.content}</p>
                        {msg.codes_extracted?.length > 0 && (
                          <div className="cp-extracted-preview">
                            <span className="cp-extracted-label">
                              <CheckCircle size={14} /> Extracted {msg.codes_extracted.length} code(s)
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {isSending && (
                    <div className="cp-message assistant loading">
                      <div className="cp-message-content">
                        <Loader2 className="spin" size={20} />
                        <span>Analyzing document...</span>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>

                {/* File Upload Preview */}
                {uploadedFiles.length > 0 && (
                  <div className="cp-upload-preview">
                    {uploadedFiles.map((file, idx) => (
                      <div key={idx} className="cp-upload-file">
                        {file.content_type?.includes('image') ? <Image size={16} /> : <FileText size={16} />}
                        <span>{file.filename}</span>
                        <button onClick={() => removeFile(idx)}>
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Input Area */}
                <div className="cp-input-area">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".pdf,image/*"
                    multiple
                    hidden
                  />
                  <button 
                    className="cp-upload-btn"
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="upload-btn"
                  >
                    <Upload size={20} />
                  </button>
                  <input
                    type="text"
                    placeholder="Ask about codes or describe what's missing..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                    disabled={isSending}
                    data-testid="chat-input"
                  />
                  <button 
                    className="cp-send-btn"
                    onClick={sendMessage}
                    disabled={isSending || (!inputMessage.trim() && uploadedFiles.length === 0)}
                    data-testid="send-btn"
                  >
                    {isSending ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Codes Panel */}
          <div className="cp-codes-panel">
            <div className="cp-codes-header">
              <h3>Extracted Codes</h3>
              <div className="cp-codes-actions">
                <button 
                  className="cp-add-code-btn"
                  onClick={() => setShowAddCode(!showAddCode)}
                  disabled={!activeSession}
                  data-testid="add-code-btn"
                >
                  <Plus size={16} /> Add
                </button>
                <button 
                  className="cp-export-btn"
                  onClick={exportCodes}
                  disabled={!activeSession || extractedCodes.length === 0}
                  data-testid="export-btn"
                >
                  <Download size={16} /> Export
                </button>
              </div>
            </div>

            {/* Add Code Search */}
            {showAddCode && (
              <div className="cp-add-code-search">
                <input
                  type="text"
                  placeholder="Search ICD-10 code or description..."
                  value={searchCode}
                  onChange={(e) => searchICD10(e.target.value)}
                  data-testid="code-search-input"
                />
                {searchResults.length > 0 && (
                  <div className="cp-search-results">
                    {searchResults.map((code, idx) => (
                      <div 
                        key={idx} 
                        className="cp-search-result"
                        onClick={() => addCode(code)}
                      >
                        <span className="cp-result-code">{code.code}</span>
                        <span className="cp-result-desc">{code.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Code Pills */}
            <div className="cp-codes-list" data-testid="codes-list">
              {extractedCodes.length === 0 ? (
                <div className="cp-no-codes">
                  <AlertCircle size={24} />
                  <p>No codes extracted yet</p>
                  <span>Upload a clinical note to begin</span>
                </div>
              ) : (
                extractedCodes.map((code, idx) => (
                  <div 
                    key={idx} 
                    className="cp-code-pill"
                    data-testid={`code-pill-${code.code}`}
                  >
                    <div className="cp-code-main">
                      <span className="cp-code-value">{code.code}</span>
                      <span className="cp-code-desc">{code.description}</span>
                    </div>
                    {code.source_text && (
                      <div className="cp-code-source">
                        <span>Source: "{code.source_text.substring(0, 50)}..."</span>
                      </div>
                    )}
                    <button 
                      className="cp-code-remove"
                      onClick={() => removeCode(code.code)}
                      data-testid={`remove-code-${code.code}`}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>

            {extractedCodes.length > 0 && (
              <div className="cp-codes-summary">
                <span>{extractedCodes.length} code(s) extracted</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClaimProcessing;
