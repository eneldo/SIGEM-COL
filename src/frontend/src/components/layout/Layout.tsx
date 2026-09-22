import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { PasswordChangeModal } from '../PasswordChangeModal'

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(() => typeof window !== 'undefined' && window.innerWidth >= 1024)

  return (
    <div className="flex min-h-screen bg-paper">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className={`flex min-h-screen flex-1 flex-col transition-[margin-left] duration-200 ease-in-out ${sidebarOpen ? 'lg:ml-64' : 'lg:ml-0'}`}>
        <Header onMenuToggle={() => setSidebarOpen((v) => !v)} />

        <main className="flex-1 px-4 py-5 sm:px-6 sm:py-7 xl:px-10 xl:py-9">
          <Outlet />
        </main>
      </div>

      <PasswordChangeModal />
    </div>
  )
}
