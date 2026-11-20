// viewer3d.js - embeds the Sketchfab "Lady justice" model (by blocula) in the hero, frames the whole figure
// and turns it slowly. Model: https://sketchfab.com/3d-models/lady-justice-4ac26e9173d5472fa342fb22903d8e9e
// The still poster underneath is the fallback if Sketchfab cannot load (offline, blocked, no WebGL).
(function () {
    'use strict';

    var holder = document.getElementById('viewer3d');
    var frame = document.getElementById('sketchfab-frame');
    if (!holder || !frame) return;

    var UID = '4ac26e9173d5472fa342fb22903d8e9e';
    var BG = [0.984, 0.969, 0.933];                       // the site's document-stock colour (#fbf7ee)
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // The model's own default view is a close-up of the base. This camera frames the whole statue.
    // (The scene is Z-up and the statue is about 7 units tall.)
    var TARGET = [-0.18, -0.27, -0.5];
    var view = { dist: 10.5, z: -0.5, angle: -0.05 };       // orbit radius, camera height, azimuth (radians)
    var SPEED = 0.32;                                     // radians per second (about 20 s per turn)

    function fail() { holder.classList.add('is-failed'); }

    var api = null, spinning = false, visible = true, lastTs = 0, lastSent = 0;

    function position() {
        return [TARGET[0] + view.dist * Math.cos(view.angle), TARGET[1] + view.dist * Math.sin(view.angle), view.z];
    }

    function tick(ts) {
        requestAnimationFrame(tick);
        var dt = Math.min((ts - lastTs) / 1000, 0.1);
        lastTs = ts;
        if (!api || !spinning || !visible || document.hidden) return;
        view.angle += SPEED * dt;
        if (ts - lastSent < 30) return;                   // about 30 updates per second is plenty
        lastSent = ts;
        api.setCameraLookAt(position(), TARGET, 0);
    }

    // While the pointer is over the model, the visitor is in charge; afterwards we continue from where they left it.
    function hold() { spinning = false; }
    function release() {
        if (!api || reduceMotion) return;
        api.getCameraLookAt(function (err, cam) {
            if (!err && cam) {
                var dx = cam.position[0] - TARGET[0], dy = cam.position[1] - TARGET[1];
                view.angle = Math.atan2(dy, dx);
                view.dist = Math.max(4, Math.min(Math.hypot(dx, dy), 30));
                view.z = cam.position[2];
            }
            spinning = true;
        });
    }
    holder.addEventListener('mouseenter', hold);
    holder.addEventListener('mouseleave', release);
    holder.addEventListener('touchstart', hold, { passive: true });
    holder.addEventListener('touchend', function () { setTimeout(release, 1800); }, { passive: true });

    function init() {
        if (typeof window.Sketchfab !== 'function') { fail(); return; }
        var client = new window.Sketchfab(frame);
        client.init(UID, {
            autostart: 1,
            preload: 1,
            dnt: 1,
            ui_controls: 0,
            ui_infos: 0,
            ui_hint: 0,
            ui_annotations: 0,
            ui_stop: 0,
            scrollwheel: 0,                                 // never hijack page scrolling
            success: function (a) {
                api = a;
                api.start();
                api.addEventListener('viewerready', function () {
                    try {
                        api.setBackground({ color: BG });
                        api.setPostProcessing({ enable: true, vignetteEnable: false });   // plain backdrop, no dark corners
                    } catch (e) { /* keep the default look */ }
                    api.setCameraLookAt(position(), TARGET, 0);
                    setTimeout(function () {
                        holder.classList.add('is-ready');
                        spinning = !reduceMotion;
                    }, 500);
                });
            },
            error: fail
        });
        setTimeout(function () { if (!holder.classList.contains('is-ready')) holder.classList.add('is-slow'); }, 15000);
    }

    var started = false;
    function begin() {
        if (started) return;
        started = true;
        var s = document.createElement('script');
        s.src = 'https://static.sketchfab.com/api/sketchfab-viewer-1.12.1.js';
        s.async = true;
        s.onload = init;
        s.onerror = fail;
        document.head.appendChild(s);
        requestAnimationFrame(tick);
    }

    if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
            visible = entries[0].isIntersecting;
            if (visible && !started) begin();
        }, { threshold: 0.05 }).observe(holder);
    } else {
        begin();
    }
})();
