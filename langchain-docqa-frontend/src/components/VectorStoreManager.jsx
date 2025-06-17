import { useEffect, useState } from 'react'
import { BiFolderOpen } from 'react-icons/bi'

export default function VectorStoreManager() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Initial fetch of files
    fetchFiles()

    // Establish WebSocket connection
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/files')

    ws.onopen = () => {
      console.log('WebSocket connection established')
    }

    ws.onmessage = event => {
      const data = JSON.parse(event.data)
      switch (data.type) {
        case 'file_updated':
          setFiles(data.files)
          break
        case 'files_cleared':
          setFiles([])
          break
      }
    }

    ws.onclose = () => {
      console.log('WebSocket connection closed')
    }

    ws.onerror = error => {
      console.error('WebSocket error:', error)
    }

    // Clean up WebSocket connection on unmount
    return () => {
      ws.close()
    }
  }, [])

  const fetchFiles = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/files')
      if (res.ok) {
        const data = await res.json()
        setFiles(data.files)
      }
    } catch (err) {
      console.error('Error fetching files:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    const confirmReset = window.confirm(
      '⚠️ WARNING: This will completely reset the application.\n\n' +
        '- All uploaded files will be deleted\n' +
        '- The vector store will be cleared\n\n' +
        'After pressing OK, you will need to manually restart both servers:\n' +
        '1. Stop the backend server (Ctrl+C)\n' +
        '2. Stop the frontend server (Ctrl+C)\n' +
        '3. Restart both servers\n\n' +
        'This action cannot be undone. Are you sure you want to continue?'
    )
    if (!confirmReset) return

    try {
      const res = await fetch('http://127.0.0.1:8000/fresh-start', {
        method: 'POST',
      })

      if (res.ok) {
        const data = await res.json()
        alert(
          `Application has been reset.\n\n${data.instructions}\n\nPlease restart both servers now.`
        )
      } else {
        throw new Error('Failed to reset application')
      }
    } catch (err) {
      console.error('Failed to perform fresh start:', err)
      alert('Failed to reset application. Please try again.')
    }
  }

  const getFileType = filename => {
    const extension = filename.split('.').pop().toLowerCase()
    const types = {
      pdf: 'PDF Document',
      docx: 'Word Document',
      txt: 'Text File',
      md: 'Markdown Document',
    }
    return types[extension] || 'Unknown Document'
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center ms-2 mt-2 gap-2">
          <BiFolderOpen className="text-yellow-500 h-6 w-6" />
          <h3 className="text-lg font-semibold">Uploaded Files</h3>
        </div>
        <button
          onClick={handleReset}
          className="px-3 py-2 me-2 mt-2 rounded-lg text-white bg-red-500 hover:bg-red-600 transition-colors"
        >
          Reset Application
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading files...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <BiFolderOpen className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-4">No files have been uploaded yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <span className="text-gray-900">{file}</span>
                  <span className="ml-auto text-xs text-gray-400">{getFileType(file)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
