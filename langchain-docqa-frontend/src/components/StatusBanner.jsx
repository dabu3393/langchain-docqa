import { useEffect, useState } from 'react'

export default function StatusBanner() {
  const [status, setStatus] = useState('loading')
  const [count, setCount] = useState(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/status')
        if (!res.ok) throw new Error('Failed to fetch')
        const data = await res.json()
        setStatus('ready')
        setCount(data.documents_indexed)
      } catch (err) {
        setStatus('error')
      }
    }

    fetchStatus()
  }, [])

  return (
    <div className="w-full bg-gray-100 py-3 px-5 rounded-md shadow-md text-center text-sm text-gray-800 border border-gray-300">
      {status === 'loading' && <span>🔄 Loading backend status...</span>}
      {status === 'ready' && <span>✅ {count} documents indexed</span>}
      {status === 'error' && <span>❌ Backend unavailable</span>}
    </div>
  )
}
