// src/components/ui/SplineScene.jsx
import { Suspense, lazy } from 'react'

const Spline = lazy(() => import('@splinetool/react-spline'))

export function SplineScene({ scene, className }) {
    return (
        <Suspense
            fallback={
                <div className="spline-loader-wrapper">
                    <span className="loader"></span>
                </div>
            }
        >
            <Spline scene={scene} className={className} />
        </Suspense>
    )
}
