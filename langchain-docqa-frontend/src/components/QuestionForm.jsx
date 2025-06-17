import { useState } from 'react'
import { BiSearch } from 'react-icons/bi'

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlight(text, query) {
    if (!query) return text
  
    // Split the question into keywords, remove empty strings
    const keywords = query
      .split(/\s+/)
      .map(word => word.replace(/[.,!?;:()"'`]+$/, '').trim())
      .filter(Boolean)

    if (!keywords.length) return text

    // Highlight each word
    const regex = new RegExp(`\\b(${keywords.map(escapeRegExp).join('|')})(['’]s)?\\b`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
}

export default function QuestionForm() {
  const [question, setQuestion] = useState('')
  const [k, setK] = useState(3)
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState(null)
  const [sources, setSources] = useState([])
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError('')
    setAnswer(null)
    setSources([])

    try {
      const res = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, k }),
      })

      if (!res.ok) {
        throw new Error('Request failed')
      }

      const data = await res.json()
      setAnswer(data.answer)
      setSources(data.sources || [])
    } catch (err) {
      setError('Failed to get answer. Please try again.')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <BiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg">
          {error}
        </div>
      )}

      {answer && (
        <div className="space-y-2">
          <h3 className="text-lg font-medium text-gray-900">Answer:</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            {answer}
          </div>
        </div>
      )}

      <div className="flex items-center justify-end space-x-2">
        <div className="relative">
          <label htmlFor="k" className="text-sm text-gray-500">No. of Snippets:</label>
          <select
            id="k"
            value={k}
            onChange={(e) => setK(parseInt(e.target.value))}
            className="ml-2 px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
          </select>
        </div>
        
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className={`
            px-4 py-2 rounded-lg text-white
            ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}
          `}
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>

      {sources.length > 0 && (
        <div className="bg-white p-3 rounded shadow text-sm mt-4">
          <strong className="block text-gray-700 mb-2">Source Snippets:</strong>
          <ul className="space-y-3">
          {sources.map((src, i) => {
              let color = "text-gray-500"
              if (src.score <= 0.3) color = "text-green-600"
              else if (src.score <= 0.5) color = "text-yellow-600"
              else color = "text-red-600"

              return (
              <li key={i} className="border-l-4 pb-2 pl-3 border-blue-200">
                  <div
                      className="mb-2 pb-2"
                      dangerouslySetInnerHTML={{ __html: highlight(src.snippet, question) }}
                  />
                  <div className="text-xs text-gray-500 flex justify-between">
                      <span className="italic">{src.source}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold
                          ${src.score <= 0.3 ? 'bg-green-100 text-green-800' :
                          src.score <= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'}
                      `}>
                          Score: {src.score?.toFixed(2) ?? 'N/A'}
                      </span>
                  </div>
              </li>
              )
          })}
          </ul>
        </div>
      )}
    </form>
  )
}
