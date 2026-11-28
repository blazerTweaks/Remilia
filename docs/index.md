---
layout: home
markdownStyles: false
title: Remilia Browser
titleTemplate: Documentation
---

<script setup>
import { withBase } from 'vitepress'
</script>

<div class="rm-home">

<section class="rm-hero" aria-labelledby="rm-title">
  <div>
    <p class="rm-eyebrow">Project SCARLET · in development</p>
    <h1 id="rm-title" class="rm-hero__title">
      <img class="rm-hero__wordmark" src="/brand/remilia-wordmark.svg" alt="Remilia" width="868" height="273">
    </h1>
    <p class="rm-hero__lead">A privacy-focused desktop browser built on Firefox (Gecko) and LibreWolf, with its own identity inspired by Remilia Scarlet.</p>
    <p class="rm-status"><strong>There is no Remilia build yet.</strong> Research is done and the build infrastructure exists. The first full build is planned once branding, security and privacy are integrated. Nothing on this site describes a shipped feature. Progress is tracked in the <a class="rm-link" :href="withBase('/project/roadmap')">roadmap</a>.</p>
    <div class="rm-actions">
      <a class="rm-button rm-button--primary" :href="withBase('/guide/overview')">Read the documentation</a>
      <a class="rm-button" href="https://github.com/ivuia/Remilia" target="_blank" rel="noreferrer">Source on GitHub <span aria-hidden="true">&#x2197;&#xFE0E;</span></a>
    </div>
  </div>
  <div class="rm-hero__art">
    <img src="/brand/remilia-mascot.svg" alt="" width="738" height="548">
  </div>
</section>

<div class="rm-divider" aria-hidden="true">
  <img src="/brand/remilia-hat.svg" alt="" width="345" height="146">
</div>

<section class="rm-section" aria-labelledby="rm-goals">
  <div class="rm-section__head">
    <p class="rm-eyebrow">Philosophy</p>
    <h2 id="rm-goals">A real browser, not a wrapper</h2>
    <p>Remilia has no browser engine of its own, wraps no WebView and is not an Electron app. Every page is rendered by Gecko, every request goes through Firefox's network stack, and every content process runs inside Firefox's Windows sandbox.</p>
  </div>
  <div>
    <ol class="rm-tenets">
      <li>
        <span class="rm-numeral" aria-hidden="true">I</span>
        <h3>A real browser</h3>
        <p>Gecko rendering, Firefox networking, multiprocess and site isolation, the Windows sandbox, and Firefox extension compatibility, all unmodified.</p>
      </li>
      <li>
        <span class="rm-numeral" aria-hidden="true">II</span>
        <h3>LibreWolf's privacy foundation</h3>
        <p>Telemetry removed at build time, Enhanced Tracking Protection Strict, Total Cookie Protection, resistFingerprinting and HTTPS-Only Mode.</p>
      </li>
      <li>
        <span class="rm-numeral" aria-hidden="true">III</span>
        <h3>uBlock Origin built in</h3>
        <p>The real, AMO-signed extension, preinstalled, with sensible default lists including regional coverage for Brazil.</p>
      </li>
      <li>
        <span class="rm-numeral" aria-hidden="true">IV</span>
        <h3>Its own identity</h3>
        <p>Original gothic, scarlet-accented branding. The reference is subtle, and the interface should look professional to people who have never heard of Touhou.</p>
      </li>
    </ol>
    <p class="rm-footnote">These are the project's design goals, not shipped features. Remilia is not an anonymity tool: what it does and does not protect against is set out in <a class="rm-link" :href="withBase('/privacy/')">Privacy</a>.</p>
  </div>
</section>

<section class="rm-section" aria-labelledby="rm-arch">
  <div class="rm-section__head">
    <p class="rm-eyebrow">Architecture</p>
    <h2 id="rm-arch">Four layers, applied in order</h2>
    <p>Remilia is a downstream build of Firefox, layered on LibreWolf's patch set and privacy configuration, with a thin, separately maintained layer of its own. Each layer is applied by script to a pristine tree. Nothing from Firefox or LibreWolf is edited by hand, which keeps upstream security releases cheap to absorb.</p>
    <a class="rm-link" :href="withBase('/browser/architecture')">Read the architecture</a>
  </div>
  <ol class="rm-layers">
    <li class="rm-layers__own">
      <span class="rm-layers__n" aria-hidden="true">4</span>
      <div>
        <span class="rm-layers__owner">Remilia</span>
        <h3>Branding and assets</h3>
        <p>Icons, wordmark, about pages, installer art and theme.</p>
      </div>
    </li>
    <li class="rm-layers__own">
      <span class="rm-layers__n" aria-hidden="true">3</span>
      <div>
        <span class="rm-layers__owner">Remilia</span>
        <h3>Build fixes, security, privacy</h3>
        <p>One directory per category, with its patches, prefs, policies and mozconfig, applied and reverted separately.</p>
      </div>
    </li>
    <li>
      <span class="rm-layers__n" aria-hidden="true">2</span>
      <div>
        <span class="rm-layers__owner">LibreWolf</span>
        <h3>Patches and privacy configuration</h3>
        <p>A pinned commit of LibreWolf's source: its patches, <code>librewolf.cfg</code>, policies and uBlock Origin assets.</p>
      </div>
    </li>
    <li>
      <span class="rm-layers__n" aria-hidden="true">1</span>
      <div>
        <span class="rm-layers__owner">Mozilla</span>
        <h3>Firefox release source</h3>
        <p>The upstream release tarball, GPG-verified against Mozilla's release key.</p>
      </div>
    </li>
  </ol>
</section>

<section class="rm-section" aria-labelledby="rm-rules">
  <div class="rm-section__head">
    <p class="rm-eyebrow">How it is built</p>
    <h2 id="rm-rules">Working rules</h2>
    <p>The rules every change to Remilia follows, from the roadmap.</p>
    <a class="rm-link" :href="withBase('/project/roadmap')">Roadmap and status</a>
  </div>
  <dl class="rm-defs">
    <div>
      <dt>Isolated change categories</dt>
      <dd>Upstream, build fixes, security, privacy and branding live in separate files and patches, never mixed in one patch or commit. Each is traceable and can be reverted on its own.</dd>
    </div>
    <div>
      <dt>A build is not a working browser</dt>
      <dd>A successful compilation only proves the build infrastructure. Nothing is called functional before the validation checklist passes and its results are recorded.</dd>
    </div>
    <div>
      <dt>The first build waits for Remilia</dt>
      <dd>The first full build is deferred until branding, security and privacy are integrated, so that it is a build of Remilia rather than of unmodified LibreWolf.</dd>
    </div>
    <div>
      <dt>No automatic phase changes</dt>
      <dd>Moving to the next phase is a maintainer decision, made after the recorded results have been reviewed.</dd>
    </div>
  </dl>
</section>

<section class="rm-section" aria-labelledby="rm-docs">
  <div class="rm-section__head">
    <p class="rm-eyebrow">Documentation</p>
    <h2 id="rm-docs">Where to read next</h2>
  </div>
  <dl class="rm-defs">
    <div>
      <dt><a :href="withBase('/browser/architecture')">Architecture</a></dt>
      <dd>Foundation choice, layer model, build pipeline, ad-block and update design.</dd>
    </div>
    <div>
      <dt><a :href="withBase('/privacy/')">Privacy</a></dt>
      <dd>Per-setting privacy evaluation and deviations from LibreWolf.</dd>
    </div>
    <div>
      <dt><a :href="withBase('/security/')">Security</a></dt>
      <dd>Security model, deviations, supply chain and open problems.</dd>
    </div>
    <div>
      <dt><a :href="withBase('/development/building')">Building</a></dt>
      <dd>Requirements and build procedure for Windows x64.</dd>
    </div>
    <div>
      <dt><a :href="withBase('/browser/upstream')">Upstream</a></dt>
      <dd>How Firefox and LibreWolf releases are tracked and absorbed.</dd>
    </div>
    <div>
      <dt><a :href="withBase('/development/contributing')">Contributing</a></dt>
      <dd>How to work on the project.</dd>
    </div>
  </dl>
</section>

</div>
