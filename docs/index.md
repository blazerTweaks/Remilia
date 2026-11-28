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
      <img class="rm-hero__wordmark" src="/brand/remilia-wordmark-3.svg" alt="Remilia" width="1756" height="588">
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

<section class="rm-goals" aria-label="Design goals">
  <ol class="rm-tenets">
    <li>
      <span class="rm-numeral" aria-hidden="true">I</span>
      <h2>A real browser</h2>
      <p>Gecko rendering, Firefox networking, multiprocess and site isolation, the Windows sandbox, and Firefox extension compatibility, all unmodified.</p>
    </li>
    <li>
      <span class="rm-numeral" aria-hidden="true">II</span>
      <h2>LibreWolf's privacy foundation</h2>
      <p>Telemetry removed at build time, Enhanced Tracking Protection Strict, Total Cookie Protection, resistFingerprinting and HTTPS-Only Mode.</p>
    </li>
    <li>
      <span class="rm-numeral" aria-hidden="true">III</span>
      <h2>uBlock Origin built in</h2>
      <p>The real, AMO-signed extension, preinstalled, with sensible default lists including regional coverage for Brazil.</p>
    </li>
    <li>
      <span class="rm-numeral" aria-hidden="true">IV</span>
      <h2>Its own identity</h2>
      <p>Original gothic, scarlet-accented branding. The reference is subtle, and the interface should look professional to people who have never heard of Touhou.</p>
    </li>
  </ol>
  <p class="rm-footnote">These are the project's design goals, not shipped features. Remilia is not an anonymity tool: what it does and does not protect against is set out in <a class="rm-link" :href="withBase('/privacy/')">Privacy</a>.</p>
</section>

</div>
