'use client'

import React from "react";
import { SplineScene } from "@/components/ui/splite";
import { Card } from "@/components/ui/card";
import { Spotlight } from "@/components/ui/spotlight";

export function SplineSceneBasic() {
    return (
        <div className="group relative w-full h-[500px]">
            {/* Rainbow Glow on Hover */}
            <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-pink-500 via-red-500 to-yellow-500 shadow-[0_0_20px_rgba(255,0,0,0.5)] via-green-500 via-purple-500 opacity-0 blur-lg group-hover:opacity-100 transition duration-1000 group-hover:duration-200"></div>

            <Card className="w-full h-[500px] bg-black/[0.96] relative overflow-hidden border-zinc-800 z-10">
                <Spotlight
                    className="-top-40 left-0 md:left-60 md:-top-20"
                    fill="white"
                />

                <div className="flex h-full">
                    {/* Left content */}
                    <div className="flex-1 p-8 relative z-10 flex flex-col justify-center">
                        <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400">
                            Interactive 3D
                        </h1>
                        <p className="mt-4 text-neutral-300 max-w-lg">
                            Bring your UI to life with beautiful 3D scenes. Create immersive experiences
                            that capture attention and enhance your design.
                        </p>
                    </div>

                    {/* Right content */}
                    <div className="flex-1 relative">
                        <SplineScene
                            scene="https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode"
                            className="w-full h-full"
                        />
                    </div>
                </div>
            </Card>
        </div>
    )
}
