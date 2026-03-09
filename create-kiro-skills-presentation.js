const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

// Theme: Midnight Executive with Teal accents
const COLORS = {
  navy: "1E2761",
  iceBlue: "CADCFC",
  white: "FFFFFF",
  teal: "028090",
  darkBg: "0F1419",
  lightBg: "F8F9FA"
};

// Configure presentation
pptx.author = "AWS";
pptx.title = "Building Kiro Skills: From Domain Expertise to Reusable AI Context";
pptx.subject = "Kiro Skills Technical Training";

// Slide 1: Title Slide (Dark)
const slide1 = pptx.addSlide();
slide1.background = { color: COLORS.navy };

slide1.addText("Building Kiro Skills", {
  x: 0.5, y: 2.0, w: 9, h: 1.2,
  fontSize: 44, bold: true, color: COLORS.white,
  align: "center"
});

slide1.addText("From Domain Expertise to Reusable AI Context", {
  x: 0.5, y: 3.3, w: 9, h: 0.6,
  fontSize: 20, color: COLORS.iceBlue,
  align: "center", italic: true
});

slide1.addText("60-Minute Technical Session for AWS SAs, TAMs & Practitioners", {
  x: 0.5, y: 5.5, w: 9, h: 0.4,
  fontSize: 14, color: COLORS.iceBlue,
  align: "center"
});

// Slide 2: The Problem (Light)
const slide2 = pptx.addSlide();
slide2.background = { color: COLORS.lightBg };

slide2.addText("The Context Gap", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});


// Problem statement with icon
slide2.addShape(pptx.shapes.OVAL, {
  x: 0.8, y: 1.8, w: 0.5, h: 0.5,
  fill: { color: COLORS.teal }
});
slide2.addText("⚠", {
  x: 0.8, y: 1.85, w: 0.5, h: 0.4,
  fontSize: 24, color: COLORS.white, align: "center"
});

slide2.addText("AI agents are only as effective as the context they carry", {
  x: 1.5, y: 1.8, w: 7.5, h: 0.5,
  fontSize: 20, bold: true, color: COLORS.navy
});

slide2.addText([
  { text: "Without structured context:\n", options: { bold: true, fontSize: 16 } },
  { text: "• Agents repeat the same mistakes\n", options: { fontSize: 14 } },
  { text: "• Domain expertise stays locked in individual heads\n", options: { fontSize: 14 } },
  { text: "• Teams rebuild solutions from scratch\n", options: { fontSize: 14 } },
  { text: "• Quality varies wildly across projects", options: { fontSize: 14 } }
], {
  x: 0.8, y: 2.8, w: 8.5, h: 2.0,
  color: "36454F", valign: "top"
});

slide2.addText("Kiro Skills close this gap", {
  x: 0.8, y: 5.2, w: 8.5, h: 0.6,
  fontSize: 18, bold: true, color: COLORS.teal, italic: true
});

// Slide 3: Learning Objectives (Light)
const slide3 = pptx.addSlide();
slide3.background = { color: COLORS.lightBg };

slide3.addText("What You'll Learn Today", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

const objectives = [
  { icon: "📐", title: "Architecture", desc: "Understand Kiro Skills architecture and how it fits in the IDE" },
  { icon: "🔍", title: "Differentiation", desc: "Skills vs. Steering vs. Powers — when to use each" },
  { icon: "✍️", title: "Design", desc: "Create domain-specific SKILL.md with proper frontmatter" },
  { icon: "📦", title: "Build", desc: "Package a complete Skill with templates and resources" },
  { icon: "🎯", title: "Control", desc: "Manage invocation, sharing, and team distribution" }
];

objectives.forEach((obj, i) => {
  const y = 1.5 + (i * 0.8);
  
  // Card background
  slide3.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.7,
    fill: { color: "FFFFFF" },
    line: { color: COLORS.teal, width: 2 }
  });
  
  // Icon circle
  slide3.addShape(pptx.shapes.OVAL, {
    x: 1.0, y: y + 0.1, w: 0.5, h: 0.5,
    fill: { color: COLORS.teal }
  });
  slide3.addText(obj.icon, {
    x: 1.0, y: y + 0.15, w: 0.5, h: 0.4,
    fontSize: 20, color: COLORS.white, align: "center"
  });
  
  // Title
  slide3.addText(obj.title, {
    x: 1.7, y: y + 0.1, w: 2.3, h: 0.5,
    fontSize: 16, bold: true, color: COLORS.navy, valign: "middle"
  });
  
  // Description
  slide3.addText(obj.desc, {
    x: 4.2, y: y + 0.1, w: 5.0, h: 0.5,
    fontSize: 14, color: "36454F", valign: "middle"
  });
});


// Slide 4: What Are Kiro Skills? (Light)
const slide4 = pptx.addSlide();
slide4.background = { color: COLORS.lightBg };

slide4.addText("What Are Kiro Skills?", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide4.addText("Portable packages of domain expertise that enhance AI agent capabilities", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 18, color: COLORS.teal, italic: true
});

// Left card - Skills are
slide4.addShape(pptx.shapes.RECTANGLE, {
  x: 0.8, y: 2.0, w: 4.2, h: 3.2,
  fill: { color: "E3F2FD" },
  line: { color: COLORS.teal, width: 3 }
});

slide4.addText("Skills are:", {
  x: 1.0, y: 2.2, w: 3.8, h: 0.4,
  fontSize: 16, bold: true, color: COLORS.navy
});

slide4.addText([
  { text: "• Markdown files with instructions\n", options: { fontSize: 14 } },
  { text: "• Automatically loaded into agent context\n", options: { fontSize: 14 } },
  { text: "• Triggered by keywords or file patterns\n", options: { fontSize: 14 } },
  { text: "• Shareable across teams and projects\n", options: { fontSize: 14 } },
  { text: "• Version-controlled like code", options: { fontSize: 14 } }
], {
  x: 1.0, y: 2.7, w: 3.8, h: 2.3,
  color: "1B5E20", valign: "top"
});

// Right card - Use Skills for
slide4.addShape(pptx.shapes.RECTANGLE, {
  x: 5.2, y: 2.0, w: 4.2, h: 3.2,
  fill: { color: "FFF3E0" },
  line: { color: "F57C00", width: 3 }
});

slide4.addText("Use Skills for:", {
  x: 5.4, y: 2.2, w: 3.8, h: 0.4,
  fontSize: 16, bold: true, color: COLORS.navy
});

slide4.addText([
  { text: "• Coding standards & patterns\n", options: { fontSize: 14 } },
  { text: "• API integration guides\n", options: { fontSize: 14 } },
  { text: "• Testing frameworks\n", options: { fontSize: 14 } },
  { text: "• Design systems\n", options: { fontSize: 14 } },
  { text: "• Domain-specific workflows", options: { fontSize: 14 } }
], {
  x: 5.4, y: 2.7, w: 3.8, h: 2.3,
  color: "E65100", valign: "top"
});

slide4.addText("Think of Skills as 'expert consultants' that join every conversation", {
  x: 0.8, y: 5.5, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

// Slide 5: Skills vs Steering vs Powers (Light)
const slide5 = pptx.addSlide();
slide5.background = { color: COLORS.lightBg };

slide5.addText("Skills vs. Steering vs. Powers", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

// Three-column comparison with cards
const features = [
  { name: "Skills", icon: "🎯", color: COLORS.teal, desc: "Specialized expertise", when: "Domain knowledge", example: "API patterns, testing frameworks" },
  { name: "Steering", icon: "🧭", color: "6D2E46", desc: "Project context", when: "Project-specific rules", example: "Build commands, team standards" },
  { name: "Powers", icon: "⚡", color: "990011", desc: "External tools", when: "New capabilities needed", example: "AWS, Figma, Postman APIs" }
];

features.forEach((f, i) => {
  const x = 0.6 + (i * 3.0);
  
  // Card background
  slide5.addShape(pptx.shapes.RECTANGLE, {
    x: x, y: 1.5, w: 2.8, h: 4.0,
    fill: { color: "FFFFFF" },
    line: { color: f.color, width: 3 }
  });
  
  // Icon circle at top
  slide5.addShape(pptx.shapes.OVAL, {
    x: x + 1.1, y: 1.8, w: 0.6, h: 0.6,
    fill: { color: f.color }
  });
  slide5.addText(f.icon, {
    x: x + 1.1, y: 1.85, w: 0.6, h: 0.5,
    fontSize: 24, color: COLORS.white, align: "center"
  });
  
  // Title
  slide5.addText(f.name, {
    x: x + 0.2, y: 2.6, w: 2.4, h: 0.4,
    fontSize: 18, bold: true, color: COLORS.navy, align: "center"
  });
  
  // Description
  slide5.addText(f.desc, {
    x: x + 0.2, y: 3.1, w: 2.4, h: 0.4,
    fontSize: 14, color: "36454F", align: "center", italic: true
  });
  
  // Divider line
  slide5.addShape(pptx.shapes.RECTANGLE, {
    x: x + 0.4, y: 3.6, w: 2.0, h: 0.02,
    fill: { color: f.color }
  });
  
  // When to use section
  slide5.addText("When to use:", {
    x: x + 0.2, y: 3.8, w: 2.4, h: 0.3,
    fontSize: 12, bold: true, color: COLORS.navy, align: "center"
  });
  slide5.addText(f.when, {
    x: x + 0.2, y: 4.1, w: 2.4, h: 0.5,
    fontSize: 12, color: "36454F", align: "center"
  });
  
  // Example section
  slide5.addText("Example:", {
    x: x + 0.2, y: 4.7, w: 2.4, h: 0.3,
    fontSize: 12, bold: true, color: COLORS.navy, align: "center"
  });
  slide5.addText(f.example, {
    x: x + 0.2, y: 5.0, w: 2.4, h: 0.6,
    fontSize: 11, color: "36454F", align: "center"
  });
});


// Slide 6: Skill Architecture (Light)
const slide6 = pptx.addSlide();
slide6.background = { color: COLORS.lightBg };

slide6.addText("Skill Architecture", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

// Left side: Structure
slide6.addText("File Structure", {
  x: 0.8, y: 1.5, w: 4.0, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.navy
});

slide6.addText([
  { text: "my-skill/\n", options: { fontFace: "Consolas", fontSize: 13, color: COLORS.teal, bold: true } },
  { text: "├── SKILL.md          ", options: { fontFace: "Consolas", fontSize: 12 } },
  { text: "# Required\n", options: { fontSize: 11, color: "990011", italic: true } },
  { text: "├── scripts/          ", options: { fontFace: "Consolas", fontSize: 12 } },
  { text: "# Executable code\n", options: { fontSize: 11, color: "666666", italic: true } },
  { text: "├── references/       ", options: { fontFace: "Consolas", fontSize: 12 } },
  { text: "# Docs loaded as needed\n", options: { fontSize: 11, color: "666666", italic: true } },
  { text: "├── assets/           ", options: { fontFace: "Consolas", fontSize: 12 } },
  { text: "# Templates, fonts, icons\n", options: { fontSize: 11, color: "666666", italic: true } },
  { text: "└── LICENSE.txt       ", options: { fontFace: "Consolas", fontSize: 12 } },
  { text: "# Optional", options: { fontSize: 11, color: "666666", italic: true } }
], {
  x: 0.8, y: 2.0, w: 4.0, h: 2.5,
  valign: "top", margin: 0
});

// Right side: Lifecycle
slide6.addText("Skill Lifecycle", {
  x: 5.2, y: 1.5, w: 4.2, h: 0.4,
  fontSize: 18, bold: true, color: COLORS.navy
});

const lifecycle = [
  { num: "1", text: "Trigger: Keyword or file match" },
  { num: "2", text: "Load: Content added to context" },
  { num: "3", text: "Execute: Agent follows instructions" },
  { num: "4", text: "Result: Consistent, expert output" }
];

lifecycle.forEach((step, i) => {
  const y = 2.0 + (i * 0.8);
  slide6.addShape(pptx.shapes.OVAL, {
    x: 5.2, y: y, w: 0.4, h: 0.4,
    fill: { color: COLORS.teal }
  });
  slide6.addText(step.num, {
    x: 5.2, y: y + 0.05, w: 0.4, h: 0.3,
    fontSize: 14, bold: true, color: COLORS.white, align: "center"
  });
  slide6.addText(step.text, {
    x: 5.8, y: y, w: 3.6, h: 0.4,
    fontSize: 14, color: "36454F"
  });
});

slide6.addText("Skills are stateless — they enhance every interaction without persistence", {
  x: 0.8, y: 5.2, w: 8.5, h: 0.5,
  fontSize: 12, color: "36454F", italic: true
});

// Slide 7: SKILL.md Anatomy (Light)
const slide7 = pptx.addSlide();
slide7.background = { color: COLORS.lightBg };

slide7.addText("SKILL.md Anatomy", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide7.addText("Every Skill starts with a SKILL.md file containing frontmatter + instructions", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

// Code example
slide7.addText([
  { text: "---\n", options: { fontFace: "Consolas", fontSize: 11, color: "999999" } },
  { text: "name: ", options: { fontFace: "Consolas", fontSize: 11, color: COLORS.teal } },
  { text: "api-integration\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "description: ", options: { fontFace: "Consolas", fontSize: 11, color: COLORS.teal } },
  { text: "REST API integration patterns\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "keywords: ", options: { fontFace: "Consolas", fontSize: 11, color: COLORS.teal } },
  { text: "[api, rest, http, integration]\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "inclusion: ", options: { fontFace: "Consolas", fontSize: 11, color: COLORS.teal } },
  { text: "auto\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "---\n\n", options: { fontFace: "Consolas", fontSize: 11, color: "999999" } },
  { text: "# API Integration Skill\n\n", options: { fontFace: "Consolas", fontSize: 11, bold: true } },
  { text: "When building API integrations:\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "- Use async/await for all HTTP calls\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "- Implement exponential backoff\n", options: { fontFace: "Consolas", fontSize: 11 } },
  { text: "- Log request/response for debugging", options: { fontFace: "Consolas", fontSize: 11 } }
], {
  x: 0.8, y: 2.0, w: 8.5, h: 3.0,
  fill: { color: "F5F5F5" },
  margin: 0.2,
  valign: "top"
});

slide7.addText("Frontmatter controls when and how the Skill activates", {
  x: 0.8, y: 5.3, w: 8.5, h: 0.4,
  fontSize: 12, color: "36454F", italic: true
});


// Slide 8: Frontmatter Fields (Light)
const slide8 = pptx.addSlide();
slide8.background = { color: COLORS.lightBg };

slide8.addText("Frontmatter Fields", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

const fields = [
  { field: "name", req: "Required", desc: "Unique identifier (lowercase, hyphens)" },
  { field: "description", req: "Required", desc: "Brief summary of what the Skill does" },
  { field: "keywords", req: "Required", desc: "Trigger words (array format)" },
  { field: "inclusion", req: "Required", desc: "auto | manual | fileMatch" },
  { field: "fileMatchPattern", req: "Optional", desc: "Glob pattern for fileMatch mode" },
  { field: "version", req: "Optional", desc: "Semantic version (e.g., 1.0.0)" }
];

// Table header background
slide8.addShape(pptx.shapes.RECTANGLE, {
  x: 0.8, y: 1.5, w: 8.5, h: 0.5,
  fill: { color: COLORS.navy }
});

// Table headers
slide8.addText("Field", {
  x: 0.9, y: 1.6, w: 2.5, h: 0.3,
  fontSize: 13, bold: true, color: COLORS.white
});

slide8.addText("Required?", {
  x: 3.5, y: 1.6, w: 1.5, h: 0.3,
  fontSize: 13, bold: true, color: COLORS.white
});

slide8.addText("Purpose", {
  x: 5.1, y: 1.6, w: 4.0, h: 0.3,
  fontSize: 13, bold: true, color: COLORS.white
});

// Table rows
fields.forEach((f, i) => {
  const y = 2.1 + (i * 0.55);
  const bgColor = i % 2 === 0 ? "FFFFFF" : "F5F5F5";
  
  // Row background
  slide8.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.5,
    fill: { color: bgColor },
    line: { color: "E0E0E0", width: 0.5 }
  });
  
  // Field name
  slide8.addText(f.field, {
    x: 0.9, y: y + 0.05, w: 2.5, h: 0.4,
    fontSize: 12, fontFace: "Consolas", color: COLORS.teal, bold: true
  });
  
  // Required status
  const reqColor = f.req === "Required" ? "990011" : "36454F";
  slide8.addText(f.req, {
    x: 3.5, y: y + 0.05, w: 1.5, h: 0.4,
    fontSize: 12, color: reqColor, bold: f.req === "Required"
  });
  
  // Description
  slide8.addText(f.desc, {
    x: 5.1, y: y + 0.05, w: 4.0, h: 0.4,
    fontSize: 11, color: "36454F"
  });
});

slide8.addText("Pro tip: Use descriptive keywords that match how developers naturally describe tasks", {
  x: 0.8, y: 5.5, w: 8.5, h: 0.4,
  fontSize: 12, color: COLORS.teal, italic: true
});

// Slide 9: Inclusion Modes (Light)
const slide9 = pptx.addSlide();
slide9.background = { color: COLORS.lightBg };

slide9.addText("Inclusion Modes", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide9.addText("Control when Skills activate with three inclusion strategies", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

const modes = [
  {
    mode: "auto",
    icon: "🔄",
    when: "Always loaded",
    use: "Core standards, universal patterns",
    example: "Code style guides, security best practices"
  },
  {
    mode: "manual",
    icon: "👆",
    when: "User invokes with #",
    use: "Specialized workflows, optional tools",
    example: "#deployment-guide, #performance-tuning"
  },
  {
    mode: "fileMatch",
    icon: "📄",
    when: "File pattern triggers",
    use: "File-type specific guidance",
    example: "*.test.js → testing patterns"
  }
];

modes.forEach((m, i) => {
  const y = 2.0 + (i * 1.15);
  
  // Card background
  slide9.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 1.0,
    fill: { color: "F5F5F5" },
    line: { color: COLORS.teal, width: 2 }
  });
  
  // Icon circle
  slide9.addShape(pptx.shapes.OVAL, {
    x: 1.0, y: y + 0.25, w: 0.5, h: 0.5,
    fill: { color: COLORS.teal }
  });
  slide9.addText(m.icon, {
    x: 1.0, y: y + 0.3, w: 0.5, h: 0.4,
    fontSize: 20, color: COLORS.white, align: "center"
  });
  
  // Mode name
  slide9.addText(m.mode, {
    x: 1.7, y: y + 0.1, w: 1.2, h: 0.35,
    fontSize: 16, bold: true, color: COLORS.navy, fontFace: "Consolas"
  });
  
  // When
  slide9.addText(m.when, {
    x: 3.0, y: y + 0.1, w: 2.0, h: 0.35,
    fontSize: 13, color: "36454F", italic: true
  });
  
  // Use case
  slide9.addText(m.use, {
    x: 1.7, y: y + 0.5, w: 7.4, h: 0.25,
    fontSize: 12, color: "36454F"
  });
  
  // Example
  slide9.addText(m.example, {
    x: 1.7, y: y + 0.75, w: 7.4, h: 0.2,
    fontSize: 11, color: "666666", fontFace: "Consolas"
  });
});


// Slide 10: Building Your First Skill (Light)
const slide10 = pptx.addSlide();
slide10.background = { color: COLORS.lightBg };

slide10.addText("Building Your First Skill", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide10.addText("5-step process from idea to deployment", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

const steps = [
  { num: "1", title: "Identify Domain", desc: "What expertise should the agent have?" },
  { num: "2", title: "Define Triggers", desc: "Keywords and file patterns that activate it" },
  { num: "3", title: "Write Instructions", desc: "Clear, actionable guidance in SKILL.md" },
  { num: "4", title: "Add Resources", desc: "Templates, examples, reference docs" },
  { num: "5", title: "Test & Iterate", desc: "Validate with real scenarios, refine" }
];

steps.forEach((step, i) => {
  const y = 2.0 + (i * 0.7);
  
  // Step card background
  slide10.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.6,
    fill: { color: "F5F5F5" },
    line: { color: COLORS.teal, width: 1 }
  });
  
  // Number circle
  slide10.addShape(pptx.shapes.OVAL, {
    x: 1.0, y: y + 0.05, w: 0.5, h: 0.5,
    fill: { color: COLORS.teal }
  });
  slide10.addText(step.num, {
    x: 1.0, y: y + 0.1, w: 0.5, h: 0.4,
    fontSize: 18, bold: true, color: COLORS.white, align: "center"
  });
  
  // Title
  slide10.addText(step.title, {
    x: 1.7, y: y + 0.05, w: 2.5, h: 0.5,
    fontSize: 16, bold: true, color: COLORS.navy, valign: "middle"
  });
  
  // Description
  slide10.addText(step.desc, {
    x: 4.4, y: y + 0.05, w: 4.7, h: 0.5,
    fontSize: 14, color: "36454F", valign: "middle"
  });
});

slide10.addText("Start simple — a single SKILL.md file is enough to provide value", {
  x: 0.8, y: 5.5, w: 8.5, h: 0.4,
  fontSize: 12, color: COLORS.teal, italic: true
});

// Slide 11: Best Practices (Light)
const slide11 = pptx.addSlide();
slide11.background = { color: COLORS.lightBg };

slide11.addText("Skill Design Best Practices", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

// Two columns with cards
slide11.addShape(pptx.shapes.RECTANGLE, {
  x: 0.8, y: 1.5, w: 4.0, h: 4.0,
  fill: { color: "E8F5E9" },
  line: { color: "2C5F2D", width: 2 }
});

slide11.addText("Do ✓", {
  x: 1.0, y: 1.7, w: 3.6, h: 0.4,
  fontSize: 18, bold: true, color: "2C5F2D"
});

slide11.addText([
  { text: "• Be specific and actionable\n", options: { fontSize: 13 } },
  { text: "• Use examples liberally\n", options: { fontSize: 13 } },
  { text: "• Include code templates\n", options: { fontSize: 13 } },
  { text: "• Test with real scenarios\n", options: { fontSize: 13 } },
  { text: "• Version your Skills\n", options: { fontSize: 13 } },
  { text: "• Document edge cases\n", options: { fontSize: 13 } },
  { text: "• Keep instructions focused", options: { fontSize: 13 } }
], {
  x: 1.0, y: 2.2, w: 3.6, h: 3.0,
  color: "1B5E20", valign: "top"
});

slide11.addShape(pptx.shapes.RECTANGLE, {
  x: 5.2, y: 1.5, w: 4.0, h: 4.0,
  fill: { color: "FFEBEE" },
  line: { color: "990011", width: 2 }
});

slide11.addText("Don't ✗", {
  x: 5.4, y: 1.7, w: 3.6, h: 0.4,
  fontSize: 18, bold: true, color: "990011"
});

slide11.addText([
  { text: "• Write vague instructions\n", options: { fontSize: 13 } },
  { text: "• Assume prior knowledge\n", options: { fontSize: 13 } },
  { text: "• Mix multiple domains\n", options: { fontSize: 13 } },
  { text: "• Skip testing\n", options: { fontSize: 13 } },
  { text: "• Overload with info\n", options: { fontSize: 13 } },
  { text: "• Forget to update\n", options: { fontSize: 13 } },
  { text: "• Use generic keywords", options: { fontSize: 13 } }
], {
  x: 5.4, y: 2.2, w: 3.6, h: 3.0,
  color: "B71C1C", valign: "top"
});

slide11.addText("Quality over quantity — one excellent Skill beats ten mediocre ones", {
  x: 0.8, y: 5.6, w: 8.5, h: 0.4,
  fontSize: 12, color: "36454F", italic: true
});


// Slide 12: Real-World Example (Light)
const slide12 = pptx.addSlide();
slide12.background = { color: COLORS.lightBg };

slide12.addText("Real-World Example: Testing Skill", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide12.addText("A practical Skill for enforcing testing standards", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

// Code example
slide12.addText([
  { text: "---\n", options: { fontFace: "Consolas", fontSize: 10, color: "999999" } },
  { text: "name: ", options: { fontFace: "Consolas", fontSize: 10, color: COLORS.teal } },
  { text: "testing-standards\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "keywords: ", options: { fontFace: "Consolas", fontSize: 10, color: COLORS.teal } },
  { text: "[test, testing, jest, vitest, unit test]\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "inclusion: ", options: { fontFace: "Consolas", fontSize: 10, color: COLORS.teal } },
  { text: "fileMatch\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "fileMatchPattern: ", options: { fontFace: "Consolas", fontSize: 10, color: COLORS.teal } },
  { text: "\"**/*.test.{js,ts}\"\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "---\n\n", options: { fontFace: "Consolas", fontSize: 10, color: "999999" } },
  { text: "# Testing Standards\n\n", options: { fontFace: "Consolas", fontSize: 10, bold: true } },
  { text: "## Test Structure\n", options: { fontFace: "Consolas", fontSize: 10, bold: true } },
  { text: "- Use describe() for grouping\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "- Use it() for individual tests\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "- Follow AAA pattern: Arrange, Act, Assert\n\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "## Coverage Requirements\n", options: { fontFace: "Consolas", fontSize: 10, bold: true } },
  { text: "- Minimum 80% line coverage\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "- Test happy path + edge cases\n", options: { fontFace: "Consolas", fontSize: 10 } },
  { text: "- Mock external dependencies", options: { fontFace: "Consolas", fontSize: 10 } }
], {
  x: 0.8, y: 2.0, w: 8.5, h: 3.0,
  fill: { color: "F5F5F5" },
  margin: 0.2,
  valign: "top"
});

slide12.addText("Result: Every time a developer opens a test file, they get expert guidance", {
  x: 0.8, y: 5.3, w: 8.5, h: 0.4,
  fontSize: 12, color: COLORS.teal, italic: true
});

// Slide 13: Sharing & Distribution (Light)
const slide13 = pptx.addSlide();
slide13.background = { color: COLORS.lightBg };

slide13.addText("Sharing & Distribution", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide13.addText("Three ways to distribute Skills across your organization", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

const distribution = [
  {
    method: "Local Installation",
    icon: "💻",
    desc: "Copy to ~/.kiro/skills/",
    pros: "Quick testing, personal use",
    cons: "Manual updates, no sync"
  },
  {
    method: "Git Repository",
    icon: "🔗",
    desc: "Clone from shared repo",
    pros: "Version control, team sync",
    cons: "Requires git workflow"
  },
  {
    method: "Marketplace",
    icon: "🏪",
    desc: "Publish to Kiro marketplace",
    pros: "Discoverable, auto-updates",
    cons: "Public visibility"
  }
];

distribution.forEach((d, i) => {
  const y = 2.0 + (i * 1.15);
  
  // Card background
  slide13.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 1.0,
    fill: { color: "F5F5F5" },
    line: { color: COLORS.teal, width: 2 }
  });
  
  // Icon
  slide13.addShape(pptx.shapes.OVAL, {
    x: 1.0, y: y + 0.25, w: 0.5, h: 0.5,
    fill: { color: COLORS.teal }
  });
  slide13.addText(d.icon, {
    x: 1.0, y: y + 0.3, w: 0.5, h: 0.4,
    fontSize: 20, color: COLORS.white, align: "center"
  });
  
  // Method
  slide13.addText(d.method, {
    x: 1.7, y: y + 0.1, w: 2.5, h: 0.35,
    fontSize: 16, bold: true, color: COLORS.navy
  });
  
  // Description
  slide13.addText(d.desc, {
    x: 4.4, y: y + 0.1, w: 4.7, h: 0.35,
    fontSize: 13, color: "36454F", italic: true
  });
  
  // Pros/Cons
  slide13.addText([
    { text: "✓ ", options: { color: "2C5F2D", fontSize: 12, bold: true } },
    { text: d.pros, options: { fontSize: 12, color: "36454F" } },
    { text: "  ✗ ", options: { color: "990011", fontSize: 12, bold: true } },
    { text: d.cons, options: { fontSize: 12, color: "36454F" } }
  ], {
    x: 1.7, y: y + 0.55, w: 7.4, h: 0.35
  });
});


// Slide 14: Team Workflow (Light)
const slide14 = pptx.addSlide();
slide14.background = { color: COLORS.lightBg };

slide14.addText("Team Workflow", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide14.addText("Recommended process for enterprise teams", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

// Process flow with cards
const workflow = [
  { step: "Create", desc: "Expert builds Skill in local environment" },
  { step: "Review", desc: "Team validates instructions and examples" },
  { step: "Commit", desc: "Push to shared Git repository" },
  { step: "Distribute", desc: "Team members clone/pull updates" },
  { step: "Iterate", desc: "Gather feedback, improve over time" }
];

workflow.forEach((w, i) => {
  const y = 2.0 + (i * 0.7);
  
  // Arrow between steps
  if (i > 0) {
    slide14.addText("↓", {
      x: 4.8, y: y - 0.35, w: 0.5, h: 0.3,
      fontSize: 24, color: COLORS.teal, align: "center", bold: true
    });
  }
  
  // Step card
  slide14.addShape(pptx.shapes.RECTANGLE, {
    x: 1.5, y: y, w: 7.0, h: 0.6,
    fill: { color: "FFFFFF" },
    line: { color: COLORS.teal, width: 2 }
  });
  
  slide14.addText(w.step, {
    x: 1.8, y: y + 0.05, w: 1.5, h: 0.5,
    fontSize: 16, bold: true, color: COLORS.navy, valign: "middle"
  });
  
  slide14.addText(w.desc, {
    x: 3.5, y: y + 0.05, w: 4.8, h: 0.5,
    fontSize: 14, color: "36454F", valign: "middle"
  });
});

slide14.addText("Treat Skills like code — version control, code review, continuous improvement", {
  x: 0.8, y: 5.6, w: 8.5, h: 0.4,
  fontSize: 12, color: COLORS.teal, italic: true
});

// Slide 15: Advanced Features (Light)
const slide15 = pptx.addSlide();
slide15.background = { color: COLORS.lightBg };

slide15.addText("Advanced Features", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

const advanced = [
  {
    feature: "File References",
    icon: "📎",
    desc: "Link to external files with #[[file:path]]",
    example: "Reference OpenAPI specs, schemas"
  },
  {
    feature: "Conditional Logic",
    icon: "🔀",
    desc: "Different instructions per context",
    example: "Dev vs. prod environments"
  },
  {
    feature: "Skill Composition",
    icon: "🧩",
    desc: "Skills can reference other Skills",
    example: "Base + specialized patterns"
  },
  {
    feature: "Template Variables",
    icon: "🔤",
    desc: "Parameterize templates",
    example: "Project name, API endpoints"
  }
];

advanced.forEach((a, i) => {
  const y = 1.6 + (i * 1.0);
  
  // Card background
  slide15.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.9,
    fill: { color: "F5F5F5" },
    line: { color: COLORS.teal, width: 2 }
  });
  
  // Icon
  slide15.addShape(pptx.shapes.OVAL, {
    x: 1.0, y: y + 0.2, w: 0.5, h: 0.5,
    fill: { color: COLORS.teal }
  });
  slide15.addText(a.icon, {
    x: 1.0, y: y + 0.25, w: 0.5, h: 0.4,
    fontSize: 20, color: COLORS.white, align: "center"
  });
  
  // Feature name
  slide15.addText(a.feature, {
    x: 1.7, y: y + 0.1, w: 2.5, h: 0.35,
    fontSize: 16, bold: true, color: COLORS.navy, valign: "middle"
  });
  
  // Description
  slide15.addText(a.desc, {
    x: 4.4, y: y + 0.1, w: 4.7, h: 0.35,
    fontSize: 13, color: "36454F", valign: "middle"
  });
  
  // Example
  slide15.addText(a.example, {
    x: 1.7, y: y + 0.5, w: 7.4, h: 0.3,
    fontSize: 11, color: "666666", italic: true
  });
});

slide15.addText("Explore these as you mature your Skill library", {
  x: 0.8, y: 5.7, w: 8.5, h: 0.4,
  fontSize: 12, color: "36454F", italic: true
});


// Slide 16: Common Use Cases (Light)
const slide16 = pptx.addSlide();
slide16.background = { color: COLORS.lightBg };

slide16.addText("Common Use Cases", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide16.addText("Skills that deliver immediate value", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

// 2x3 grid
const useCases = [
  { title: "Code Standards", desc: "Linting rules, formatting, naming conventions" },
  { title: "API Patterns", desc: "REST/GraphQL integration, error handling" },
  { title: "Testing", desc: "Unit test structure, mocking, coverage" },
  { title: "Security", desc: "Auth patterns, input validation, secrets" },
  { title: "Documentation", desc: "README templates, API docs, comments" },
  { title: "Deployment", desc: "CI/CD workflows, environment configs" }
];

useCases.forEach((uc, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.8 + (col * 4.5);
  const y = 2.0 + (row * 1.2);
  
  // Card background
  slide16.addShape(pptx.shapes.RECTANGLE, {
    x: x, y: y, w: 4.2, h: 1.0,
    fill: { color: "F5F5F5" },
    line: { color: COLORS.teal, width: 1 }
  });
  
  // Title
  slide16.addText(uc.title, {
    x: x + 0.2, y: y + 0.15, w: 3.8, h: 0.3,
    fontSize: 15, bold: true, color: COLORS.navy
  });
  
  // Description
  slide16.addText(uc.desc, {
    x: x + 0.2, y: y + 0.5, w: 3.8, h: 0.4,
    fontSize: 12, color: "36454F"
  });
});

slide16.addText("Start with your team's most frequent questions or repeated mistakes", {
  x: 0.8, y: 5.3, w: 8.5, h: 0.4,
  fontSize: 12, color: COLORS.teal, italic: true
});

// Slide 17: Measuring Success (Light)
const slide17 = pptx.addSlide();
slide17.background = { color: COLORS.lightBg };

slide17.addText("Measuring Success", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

slide17.addText("How to know if your Skills are working", {
  x: 0.8, y: 1.4, w: 8.5, h: 0.4,
  fontSize: 14, color: "36454F", italic: true
});

const metrics = [
  {
    metric: "Adoption Rate",
    measure: "% of team using Skills",
    target: "> 80% within 30 days"
  },
  {
    metric: "Code Quality",
    measure: "Fewer review comments",
    target: "30% reduction"
  },
  {
    metric: "Consistency",
    measure: "Pattern adherence",
    target: "90%+ compliance"
  },
  {
    metric: "Time Savings",
    measure: "Task completion speed",
    target: "20% faster"
  },
  {
    metric: "Knowledge Transfer",
    measure: "Junior dev productivity",
    target: "Faster onboarding"
  }
];

// Table header background
slide17.addShape(pptx.shapes.RECTANGLE, {
  x: 0.8, y: 2.0, w: 8.5, h: 0.5,
  fill: { color: COLORS.navy }
});

// Table headers
slide17.addText("Metric", {
  x: 0.9, y: 2.1, w: 2.3, h: 0.3,
  fontSize: 13, bold: true, color: COLORS.white
});

slide17.addText("How to Measure", {
  x: 3.4, y: 2.1, w: 3.0, h: 0.3,
  fontSize: 13, bold: true, color: COLORS.white
});

slide17.addText("Target", {
  x: 6.6, y: 2.1, w: 2.5, h: 0.3,
  fontSize: 13, bold: true, color: COLORS.white
});

// Table rows
metrics.forEach((m, i) => {
  const y = 2.6 + (i * 0.55);
  const bgColor = i % 2 === 0 ? "FFFFFF" : "F5F5F5";
  
  // Row background
  slide17.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.5,
    fill: { color: bgColor },
    line: { color: "E0E0E0", width: 0.5 }
  });
  
  // Metric name
  slide17.addText(m.metric, {
    x: 0.9, y: y + 0.05, w: 2.3, h: 0.4,
    fontSize: 12, bold: true, color: COLORS.navy
  });
  
  // Measure
  slide17.addText(m.measure, {
    x: 3.4, y: y + 0.05, w: 3.0, h: 0.4,
    fontSize: 12, color: "36454F"
  });
  
  // Target
  slide17.addText(m.target, {
    x: 6.6, y: y + 0.05, w: 2.5, h: 0.4,
    fontSize: 12, color: COLORS.teal, bold: true
  });
});

slide17.addText("Track qualitative feedback too — ask developers what's working", {
  x: 0.8, y: 5.5, w: 8.5, h: 0.4,
  fontSize: 12, color: "36454F", italic: true
});


// Slide 18: Troubleshooting (Light)
const slide18 = pptx.addSlide();
slide18.background = { color: COLORS.lightBg };

slide18.addText("Common Issues & Solutions", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

const issues = [
  {
    problem: "Skill not activating",
    solution: "Check keywords match, verify inclusion mode, restart IDE"
  },
  {
    problem: "Instructions ignored",
    solution: "Be more specific, add examples, reduce ambiguity"
  },
  {
    problem: "Conflicts with other Skills",
    solution: "Use more specific keywords, adjust inclusion patterns"
  },
  {
    problem: "Too much context",
    solution: "Split into focused Skills, use manual inclusion"
  },
  {
    problem: "Outdated guidance",
    solution: "Version Skills, document update process"
  }
];

issues.forEach((issue, i) => {
  const y = 1.7 + (i * 0.8);
  
  // Card background
  slide18.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.7,
    fill: { color: "FFF3E0" },
    line: { color: "F57C00", width: 2 }
  });
  
  // Problem icon
  slide18.addText("⚠", {
    x: 1.0, y: y + 0.1, w: 0.4, h: 0.5,
    fontSize: 18, color: "990011", valign: "middle"
  });
  
  // Problem
  slide18.addText(issue.problem, {
    x: 1.6, y: y + 0.1, w: 3.0, h: 0.5,
    fontSize: 14, bold: true, color: COLORS.navy, valign: "middle"
  });
  
  // Arrow
  slide18.addText("→", {
    x: 4.7, y: y + 0.1, w: 0.3, h: 0.5,
    fontSize: 16, color: COLORS.teal, align: "center", valign: "middle"
  });
  
  // Solution
  slide18.addText(issue.solution, {
    x: 5.1, y: y + 0.1, w: 4.0, h: 0.5,
    fontSize: 13, color: "36454F", valign: "middle"
  });
});

slide18.addText("Most issues stem from unclear instructions or overly broad triggers", {
  x: 0.8, y: 5.8, w: 8.5, h: 0.4,
  fontSize: 12, color: "36454F", italic: true
});

// Slide 19: Resources (Light)
const slide19 = pptx.addSlide();
slide19.background = { color: COLORS.lightBg };

slide19.addText("Resources & Next Steps", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

const resources = [
  {
    icon: "📚",
    title: "Documentation",
    items: ["kiro.dev/docs/skills", "agentskills.io/specification"]
  },
  {
    icon: "💡",
    title: "Examples",
    items: ["github.com/kiro-skills", "Community marketplace"]
  },
  {
    icon: "👥",
    title: "Community",
    items: ["Kiro Discord", "AWS internal Slack"]
  },
  {
    icon: "🎯",
    title: "Practice",
    items: ["Build your first Skill today", "Start with one domain"]
  }
];

resources.forEach((r, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const x = 0.8 + (col * 4.5);
  const y = 1.6 + (row * 1.9);
  
  // Card background
  slide19.addShape(pptx.shapes.RECTANGLE, {
    x: x, y: y, w: 4.2, h: 1.7,
    fill: { color: "FFFFFF" },
    line: { color: COLORS.teal, width: 3 }
  });
  
  // Icon circle at top
  slide19.addShape(pptx.shapes.OVAL, {
    x: x + 1.8, y: y + 0.2, w: 0.6, h: 0.6,
    fill: { color: COLORS.teal }
  });
  slide19.addText(r.icon, {
    x: x + 1.8, y: y + 0.25, w: 0.6, h: 0.5,
    fontSize: 24, color: COLORS.white, align: "center"
  });
  
  // Title
  slide19.addText(r.title, {
    x: x + 0.2, y: y + 0.9, w: 3.8, h: 0.35,
    fontSize: 16, bold: true, color: COLORS.navy, align: "center"
  });
  
  // Items
  r.items.forEach((item, j) => {
    slide19.addText("• " + item, {
      x: x + 0.3, y: y + 1.3 + (j * 0.25), w: 3.6, h: 0.22,
      fontSize: 12, color: "36454F"
    });
  });
});

slide19.addText("The best way to learn is to build — start with one Skill this week", {
  x: 0.8, y: 5.5, w: 8.5, h: 0.4,
  fontSize: 12, color: COLORS.teal, italic: true
});


// Slide 20: Key Takeaways (Light)
const slide20 = pptx.addSlide();
slide20.background = { color: COLORS.lightBg };

slide20.addText("Key Takeaways", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 36, bold: true, color: COLORS.navy
});

const takeaways = [
  "Skills turn domain expertise into reusable AI context",
  "Start simple — a single SKILL.md file provides value",
  "Use frontmatter to control when Skills activate",
  "Treat Skills like code — version, review, iterate",
  "Measure success through adoption and quality metrics"
];

takeaways.forEach((takeaway, i) => {
  const y = 1.6 + (i * 0.75);
  
  // Card background
  slide20.addShape(pptx.shapes.RECTANGLE, {
    x: 0.8, y: y, w: 8.5, h: 0.65,
    fill: { color: "FFFFFF" },
    line: { color: COLORS.teal, width: 2 }
  });
  
  // Number circle
  slide20.addShape(pptx.shapes.OVAL, {
    x: 1.0, y: y + 0.08, w: 0.5, h: 0.5,
    fill: { color: COLORS.teal }
  });
  slide20.addText((i + 1).toString(), {
    x: 1.0, y: y + 0.13, w: 0.5, h: 0.4,
    fontSize: 20, bold: true, color: COLORS.white, align: "center"
  });
  
  // Takeaway text
  slide20.addText(takeaway, {
    x: 1.7, y: y + 0.08, w: 7.4, h: 0.5,
    fontSize: 16, color: "36454F", valign: "middle"
  });
});

slide20.addText("Skills scale expertise — build once, benefit everywhere", {
  x: 0.8, y: 5.5, w: 8.5, h: 0.4,
  fontSize: 14, color: COLORS.teal, italic: true, bold: true
});

// Slide 21: Closing (Dark)
const slide21 = pptx.addSlide();
slide21.background = { color: COLORS.navy };

slide21.addText("Thank You", {
  x: 0.5, y: 2.0, w: 9, h: 1.0,
  fontSize: 44, bold: true, color: COLORS.white,
  align: "center"
});

slide21.addText("Questions?", {
  x: 0.5, y: 3.2, w: 9, h: 0.6,
  fontSize: 24, color: COLORS.iceBlue,
  align: "center"
});

slide21.addText([
  { text: "Start building your first Skill today\n", options: { fontSize: 16, color: COLORS.iceBlue } },
  { text: "kiro.dev/docs/skills", options: { fontSize: 14, color: COLORS.white, italic: true } }
], {
  x: 0.5, y: 4.5, w: 9, h: 0.8,
  align: "center"
});

// Save presentation
pptx.writeFile({ fileName: "Kiro-Skills-Technical-Training.pptx" })
  .then(() => {
    console.log("✓ Presentation created: Kiro-Skills-Technical-Training.pptx");
  })
  .catch((err) => {
    console.error("Error creating presentation:", err);
  });
