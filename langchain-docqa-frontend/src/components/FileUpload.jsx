import { useState } from 'react'
import { BiCloudUpload } from 'react-icons/bi'

export default function FileUpload() {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleDrop = async e => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      await handleFile(file)
    }
  }

  const handleFile = async file => {
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        throw new Error('Upload failed')
      }

      const data = await res.json()
      console.log('Upload successful:', data)
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleDragOver = e => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleFileSelect = e => {
    const file = e.target.files[0]
    if (file) {
      handleFile(file)
    }
  }

  const handleAreaClick = () => {
    document.getElementById('fileInput').click()
  }

  return (
    <div
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-all duration-300
        ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-500 hover:bg-blue-50'}
        ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleAreaClick}
    >
      <BiCloudUpload className="mx-auto h-12 w-12 text-gray-400" />
      <h3 className="mt-4 text-lg font-medium text-gray-900">Drop files here or click to upload</h3>
      <p className="mt-2 text-sm text-gray-500">PDF, MD, TXT files up to 10MB</p>

      <input
        type="file"
        id="fileInput"
        className="hidden"
        onChange={handleFileSelect}
        accept=".pdf,.md,.txt"
      />

      {uploading && (
        <div className="mt-4">
          <div className="h-1 bg-blue-500 rounded-full w-1/2 mx-auto"></div>
          <p className="mt-2 text-sm text-blue-600">Uploading...</p>
        </div>
      )}
    </div>
  )
}
