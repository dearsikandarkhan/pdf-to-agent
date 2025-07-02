import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

function App() {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [question, setQuestion] = useState('');
  const [docId, setDocId] = useState('');
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');
  const [typing, setTyping] = useState(false);

  useEffect(() => {
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setFileName(e.target.files[0].name);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post('http://localhost:8000/upload', formData);
      setDocId(res.data.doc_id);
      setChat([{ role: 'system', message: `✅ File uploaded: ${fileName}. You can now ask questions.` }]);
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    }
    setLoading(false);
  };

  const handleAsk = async () => {
    if (!question || !docId) return;
    setLoading(true);
    setTyping(true);
    const formData = new FormData();
    formData.append('doc_id', docId);
    formData.append('question', question);
    try {
      const res = await axios.post('http://localhost:8000/ask', formData);
      const timestamp = new Date().toLocaleTimeString();
      setChat(prev => [
        ...prev,
        { role: 'user', message: question, time: timestamp },
        { role: 'ai', message: res.data.answer, time: timestamp }
      ]);
      setQuestion('');
    } catch (err) {
      console.error(err);
      alert('Error getting answer');
    }
    setLoading(false);
    setTyping(false);
  };

  const renderAvatar = (role) => {
    if (role === 'user') return <span className="mr-2">🧑‍💻</span>;
    if (role === 'ai') return <span className="ml-2">🤖</span>;
    return null;
  };

  const renderBubble = (msg, index) => {
    let align = 'justify-start';
    let bg = 'bg-gray-300';
    let sender = 'User';

    if (msg.role === 'ai') {
      align = 'justify-end';
      bg = 'bg-green-200';
      sender = 'AI';
    } else if (msg.role === 'system') {
      align = 'justify-center';
      bg = 'bg-blue-100';
      sender = '';
    }

    return (
      <div key={index} className={`flex ${align} mb-2 items-start`}>
        {msg.role === 'user' && renderAvatar('user')}
        <div className={`p-3 rounded-xl max-w-xs ${bg}`}> 
          {sender && <p className="text-xs font-semibold mb-1">{sender} {msg.time && <span className="text-xs text-gray-500 ml-1">{msg.time}</span>}</p>}
          <ReactMarkdown className="text-sm whitespace-pre-wrap">{msg.message}</ReactMarkdown>
        </div>
        {msg.role === 'ai' && renderAvatar('ai')}
      </div>
    );
  };

  return (
    <div className={`${darkMode ? 'bg-gray-900 text-white' : 'bg-white text-black'} min-h-screen p-8`}> 
      <div className="max-w-xl mx-auto">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">📄 PDF to AI Agent</h1>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="text-sm px-3 py-1 border rounded"
          >
            {darkMode ? '☀️ Light' : '🌙 Dark'}
          </button>
        </div>

        <div className="mb-2">
          <input type="file" onChange={handleFileChange} className="mb-1" />
          {fileName && <p className="text-sm text-gray-500">📎 {fileName}</p>}
        </div>

        <button onClick={handleUpload} className="bg-blue-600 text-white px-4 py-2 rounded mb-4">
          Upload PDF
        </button>

        <div className="mb-4">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask something about the PDF..."
            className="w-full border px-3 py-2 text-black"
          />
          <button onClick={handleAsk} className="bg-green-600 text-white px-4 py-2 rounded mt-2">
            Ask
          </button>
        </div>

        <div className={`p-4 rounded h-96 overflow-auto ${darkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
          {chat.map((msg, index) => renderBubble(msg, index))}
          {typing && <p className="text-center animate-pulse">🤖 Typing...</p>}
        </div>
      </div>
    </div>
  );
}

export default App;