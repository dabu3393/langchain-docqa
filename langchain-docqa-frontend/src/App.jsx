import FileUpload from './components/FileUpload'
import QuestionForm from './components/QuestionForm'
import VectorStoreManager from './components/VectorStoreManager'

function App() {
  return (
    <div className="min-h-screen bg-gray-200 flex">
      <div className="w-full max-w-7xl mx-auto">
        <div className="grid grid-cols-10 gap-6 mt-6 p-6">
          {/* Left side (70%) */}
          <div className="col-span-7 bg-white rounded-lg shadow">
            {/* File Upload (top) */}
            <div className="p-6 border-b">
              <FileUpload />
            </div>

            {/* Question Form (bottom) */}
            <div className="p-6">
              <QuestionForm />
            </div>
          </div>

          {/* Right side (30%) */}
          <div className="col-span-3 bg-white rounded-lg shadow">
            <VectorStoreManager />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
