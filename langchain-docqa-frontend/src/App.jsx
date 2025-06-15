import StatusBanner from './components/StatusBanner'

function App() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <StatusBanner />
        {/* Other components like the question form will go here later */}
      </div>
    </div>
  )
}

export default App
