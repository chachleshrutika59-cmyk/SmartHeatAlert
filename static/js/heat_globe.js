const container = document.getElementById("heat-globe");

if (container) {
    const canvas = container.querySelector(".globe-canvas");
    const fallback = container.querySelector(".globe-fallback");
    const latitude = Number(container.dataset.latitude);
    const longitude = Number(container.dataset.longitude);
    const temperature = container.dataset.temperature
        ? Number(container.dataset.temperature)
        : Number.NaN;
    const hasLocation =
        container.dataset.latitude !== "" &&
        container.dataset.longitude !== "" &&
        Number.isFinite(latitude) &&
        Number.isFinite(longitude) &&
        latitude >= -90 &&
        latitude <= 90 &&
        longitude >= -180 &&
        longitude <= 180;
    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    if (
        hasLocation &&
        canvas &&
        fallback &&
        "WebGLRenderingContext" in window
    ) {
        let renderer;
        let scene;
        let camera;
        let globeGroup;
        let marker;
        let waveRings = [];
        let frameId = null;
        let isVisible = false;
        let isPageVisible = !document.hidden;
        let resizeObserver;
        let isLoading = false;

        const latLngVector = (latDegrees, lonDegrees, radius, THREE) => {
            const lat = THREE.MathUtils.degToRad(latDegrees);
            const lon = THREE.MathUtils.degToRad(lonDegrees);

            return new THREE.Vector3(
                radius * Math.cos(lat) * Math.sin(lon),
                radius * Math.sin(lat),
                radius * Math.cos(lat) * Math.cos(lon)
            );
        };

        const heatColor = (value, THREE) => {
            if (!Number.isFinite(value)) {
                return new THREE.Color("#ef9e54");
            }

            const amount = THREE.MathUtils.clamp((value - 20) / 25, 0, 1);
            return new THREE.Color("#64c6a4").lerp(
                new THREE.Color("#f0643b"),
                amount
            );
        };

        const makeLine = (points, material, THREE, closed = false) => {
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const line = closed
                ? new THREE.LineLoop(geometry, material)
                : new THREE.Line(geometry, material);
            globeGroup.add(line);
        };

        const addGlobeGrid = (THREE) => {
            const gridMaterial = new THREE.LineBasicMaterial({
                color: "#91c7c5",
                transparent: true,
                opacity: 0.18
            });
            const radius = 1.006;
            const divisions = 48;

            for (let lat = -60; lat <= 60; lat += 30) {
                const points = [];
                for (let step = 0; step < divisions; step += 1) {
                    points.push(
                        latLngVector(lat, -180 + (360 * step) / divisions, radius, THREE)
                    );
                }
                makeLine(points, gridMaterial, THREE, true);
            }

            for (let lon = -150; lon <= 180; lon += 30) {
                const points = [];
                for (let step = 0; step <= divisions; step += 1) {
                    points.push(
                        latLngVector(-90 + (180 * step) / divisions, lon, radius, THREE)
                    );
                }
                makeLine(points, gridMaterial, THREE);
            }
        };

        const renderOnce = () => {
            if (!renderer || !scene || !camera) {
                return;
            }

            const { clientWidth, clientHeight } = canvas;
            if (!clientWidth || !clientHeight) {
                return;
            }

            renderer.setSize(clientWidth, clientHeight, false);
            camera.aspect = clientWidth / clientHeight;
            camera.updateProjectionMatrix();
            renderer.render(scene, camera);
        };

        const stopAnimation = () => {
            if (frameId !== null) {
                window.cancelAnimationFrame(frameId);
                frameId = null;
            }
        };

        const animate = (time) => {
            frameId = null;
            if (!isVisible || !isPageVisible || !renderer) {
                return;
            }

            if (!reducedMotion) {
                globeGroup.rotation.y = time * 0.000045;
                const elapsed = time * 0.00035;
                waveRings.forEach((ring, index) => {
                    const phase = (elapsed + index / waveRings.length) % 1;
                    const scale = 0.85 + phase * 1.25;
                    ring.mesh.scale.setScalar(scale);
                    ring.material.opacity = (1 - phase) * 0.44;
                });
            }

            renderOnce();
            if (!reducedMotion) {
                frameId = window.requestAnimationFrame(animate);
            }
        };

        const startAnimation = () => {
            if (!isVisible || !isPageVisible || frameId !== null) {
                return;
            }
            frameId = window.requestAnimationFrame(animate);
        };

        const buildGlobe = async () => {
            if (renderer || isLoading) {
                return;
            }
            isLoading = true;

            try {
                const THREE = await import(
                    "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js"
                );
                if (!container.isConnected) {
                    return;
                }

                renderer = new THREE.WebGLRenderer({
                    canvas,
                    alpha: true,
                    antialias: false,
                    powerPreference: "low-power"
                });
                renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
                renderer.setClearColor(0x000000, 0);

                scene = new THREE.Scene();
                camera = new THREE.PerspectiveCamera(38, 1, 0.1, 20);
                camera.position.set(0, 0, 4.4);
                globeGroup = new THREE.Group();
                scene.add(globeGroup);

                scene.add(new THREE.AmbientLight("#d9f2e9", 1.25));
                const keyLight = new THREE.DirectionalLight("#fff0d7", 2.1);
                keyLight.position.set(-3, 3, 4);
                scene.add(keyLight);

                const globe = new THREE.Mesh(
                    new THREE.SphereGeometry(1, 32, 24),
                    new THREE.MeshStandardMaterial({
                        color: "#184755",
                        roughness: 0.82,
                        metalness: 0.04
                    })
                );
                globeGroup.add(globe);
                addGlobeGrid(THREE);

                const markerColor = heatColor(temperature, THREE);
                const markerPosition = latLngVector(
                    latitude,
                    longitude,
                    1.025,
                    THREE
                );
                const markerNormal = markerPosition.clone().normalize();
                const markerMaterial = new THREE.MeshStandardMaterial({
                    color: markerColor,
                    emissive: markerColor,
                    emissiveIntensity: 0.65,
                    roughness: 0.35
                });

                marker = new THREE.Mesh(
                    new THREE.SphereGeometry(0.045, 12, 10),
                    markerMaterial
                );
                marker.position.copy(markerPosition);
                globeGroup.add(marker);

                const ringGroup = new THREE.Group();
                ringGroup.position.copy(
                    markerNormal.clone().multiplyScalar(1.018)
                );
                ringGroup.quaternion.setFromUnitVectors(
                    new THREE.Vector3(0, 1, 0),
                    markerNormal
                );
                globeGroup.add(ringGroup);

                for (let index = 0; index < 3; index += 1) {
                    const material = new THREE.MeshBasicMaterial({
                        color: markerColor,
                        transparent: true,
                        opacity: 0.35,
                        side: THREE.DoubleSide,
                        depthWrite: false
                    });
                    const mesh = new THREE.Mesh(
                        new THREE.RingGeometry(0.065, 0.078, 28),
                        material
                    );
                    mesh.position.y = index * 0.001;
                    ringGroup.add(mesh);
                    waveRings.push({ mesh, material });
                }

                container.classList.add("globe-ready");
                renderOnce();
                startAnimation();

                resizeObserver = new ResizeObserver(renderOnce);
                resizeObserver.observe(canvas);
                canvas.addEventListener("webglcontextlost", () => {
                    stopAnimation();
                    resizeObserver?.disconnect();
                    renderer?.dispose();
                    renderer = null;
                    container.classList.remove("globe-ready");
                }, { once: true });
            } catch (error) {
                renderer?.dispose();
                renderer = null;
                container.classList.remove("globe-ready");
                console.warn(
                    "HeatGuard globe initialization failed; displaying the static fallback.",
                    error
                );
            } finally {
                isLoading = false;
            }
        };

        const visibilityObserver = new IntersectionObserver((entries) => {
            isVisible = entries.some((entry) => entry.isIntersecting);
            if (isVisible) {
                buildGlobe();
                startAnimation();
            } else {
                stopAnimation();
            }
        }, { rootMargin: "100px" });
        visibilityObserver.observe(container);

        document.addEventListener("visibilitychange", () => {
            isPageVisible = !document.hidden;
            if (isPageVisible) {
                startAnimation();
            } else {
                stopAnimation();
            }
        });
    }
}
