import React from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const Arrow = () => <svg aria-hidden="true" viewBox="0 0 18 18" className="arrow"><path d="M3.5 9h10M9.5 4.5 14 9l-4.5 4.5" /></svg>;

function App() {
  return <main className="page-shell">
    <nav className="nav container" aria-label="Main navigation">
      <a className="brand" href="#top" aria-label="GDG AI Grader home"><span className="brand-mark">G</span><span>GDG <em>AI</em> Grader</span></a>
      <div className="nav-links"><a href="#how-it-works">How it works</a><a href="#about">About</a><a className="nav-button" href="#get-started">Sign in <Arrow /></a></div>
    </nav>

    <section className="hero container" id="top">
      <div className="hero-copy">
        <div className="eyebrow"><span className="eyebrow-line" /> OPEN SOURCE · HUMAN REVIEW</div>
        <h1>Grading that gives <span>everyone</span> a fair shot.</h1>
        <p className="hero-text">An open-source assistant for thoughtful assessment. Let AI handle the first pass while educators stay in control of every final grade.</p>
        <div className="hero-actions" id="get-started"><a className="button button-primary" href="#workspace">Open workspace <Arrow /></a><a className="text-link" href="#how-it-works">See how it works <Arrow /></a></div>
        <div className="trust-note"><span className="pulse" /> Your grades stay yours. Always.</div>
      </div>

      <div className="hero-visual" aria-label="Example grading review panel">
        <div className="orb orb-one" /><div className="orb orb-two" />
        <div className="review-card">
          <div className="review-topline"><span>REVIEW QUEUE</span><span className="queue-count">03 pending</span></div>
          <div className="review-heading"><h2>Literary analysis</h2><span className="dots">•••</span></div>
          <div className="student-row"><span className="avatar">AM</span><span><strong>Alex Morgan</strong><small>Submitted 12 min ago</small></span><span className="review-status">Needs review</span></div>
          <div className="score-band"><div><small>AI SUGGESTED SCORE</small><strong>84<span>/100</span></strong></div><div className="score-ring"><span>84%</span></div></div>
          <div className="feedback"><span className="feedback-dot" /><span>Strong argument with clear evidence. Consider expanding the conclusion.</span></div>
          <div className="card-actions"><button className="approve">Approve grade</button><button className="edit">Edit feedback</button></div>
        </div>
        <div className="floating-tag tag-top"><span className="tag-icon">✦</span> AI-assisted</div><div className="floating-tag tag-bottom"><span className="check">✓</span> Human approved</div>
      </div>
    </section>

    <section className="proof-strip" id="how-it-works"><div className="container proof-inner"><p>BUILT FOR BETTER FEEDBACK</p><div className="proof-items"><span>01 <b>Upload</b> your exam</span><i /><span>02 <b>Review</b> suggestions</span><i /><span>03 <b>Share</b> clear feedback</span></div></div></section>
    <section className="principles container" id="about"><div><p className="eyebrow">OUR APPROACH</p><h2>Helpful by design.<br /><span>Human at the center.</span></h2></div><div className="principle-copy"><p>Grading is more than a score. GDG AI Grader helps you spend less time on repetitive work and more time on the feedback that helps learners grow.</p><a className="text-link" href="#workspace">Explore the workspace <Arrow /></a></div></section>
    <footer className="container footer" id="workspace"><span>© 2025 GDG AI Grader</span><span>Open source · Built for learners and educators</span></footer>
  </main>;
}

createRoot(document.getElementById('root')).render(<App />);
