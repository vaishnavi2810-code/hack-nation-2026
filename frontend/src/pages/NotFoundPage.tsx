import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

const STATUS_CODE = '404'
const PAGE_TITLE = 'Page not found'
const PAGE_SUBTITLE = "This doctor portal page doesn't exist."
const LINK_PATH = '/login'
const LINK_LABEL = 'Back to login'

const NotFoundPage = () => {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="text-center">
        <p className="text-sm font-semibold text-primary">{STATUS_CODE}</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">{PAGE_TITLE}</h1>
        <p className="mt-2 text-sm text-slate-600">{PAGE_SUBTITLE}</p>
        <Link
          to={LINK_PATH}
          className="mt-6 inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-primary hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          {LINK_LABEL}
        </Link>
      </div>
    </div>
  )
}

export default NotFoundPage
