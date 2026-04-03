/**
 * A2UI Renderer for Nester AI Voice Assistant
 *
 * Renders A2UI visual components into DOM elements based on template type.
 * Supports all A2UI v1 template formats.
 */

import type {
  A2UIDocument,
  A2UITemplateType,
  TemplateGridProps,
  TimelineProps,
  ContactCardProps,
  ComparisonChartProps,
  StatsFlowLayoutProps,
  StatsChartProps,
  TeamFlipCardsProps,
  ServiceHoverRevealProps,
  MagazineHeroProps,
  FAQAccordionProps,
  BlogMagazineProps,
  ImageGalleryProps,
  VideoGalleryProps,
  SalesDashboardProps,
} from '../../types/a2ui';

/**
 * A2UI Renderer class - renders A2UI documents to DOM elements
 */
export class A2UIRenderer {
  private container: HTMLElement;

  constructor(containerId: string) {
    const element = document.getElementById(containerId);
    if (!element) {
      console.error(`[A2UI] Container not found: ${containerId}`);
      throw new Error(`A2UI container element not found: ${containerId}`);
    }
    this.container = element;
  }

  /**
   * Render an A2UI document
   */
  render(doc: A2UIDocument): void {
    if (!doc || !doc.root) {
      console.warn('[A2UI] Invalid document - missing doc or doc.root');
      return;
    }

    const templateType = doc.root.type;
    const props = doc.root.props;
    const metadata = doc._metadata;


    // Clear previous content
    this.container.innerHTML = '';

    // Create wrapper with animation
    const wrapper = document.createElement('div');
    wrapper.className = 'a2ui-wrapper a2ui-fade-in';

    // Route to appropriate renderer
    switch (templateType) {
      case 'template-grid':
        wrapper.appendChild(this.renderTemplateGrid(props as TemplateGridProps));
        break;
      case 'timeline':
        wrapper.appendChild(this.renderTimeline(props as TimelineProps));
        break;
      case 'contact-card':
        wrapper.appendChild(this.renderContactCard(props as ContactCardProps));
        break;
      case 'comparison-chart':
        wrapper.appendChild(this.renderComparisonChart(props as ComparisonChartProps));
        break;
      case 'stats-flow-layout':
        wrapper.appendChild(this.renderStatsFlowLayout(props as StatsFlowLayoutProps));
        break;
      case 'team-flip-cards':
        wrapper.appendChild(this.renderTeamFlipCards(props as TeamFlipCardsProps));
        break;
      case 'service-hover-reveal':
        wrapper.appendChild(this.renderServiceHoverReveal(props as ServiceHoverRevealProps));
        break;
      case 'magazine-hero':
        wrapper.appendChild(this.renderMagazineHero(props as MagazineHeroProps));
        break;
      case 'faq-accordion':
        wrapper.appendChild(this.renderFAQAccordion(props as FAQAccordionProps));
        break;
      case 'image-gallery':
        wrapper.appendChild(this.renderImageGallery(props as ImageGalleryProps));
        break;
      case 'video-gallery':
        wrapper.appendChild(this.renderVideoGallery(props as VideoGalleryProps));
        break;
      case 'stats-chart':
        wrapper.appendChild(this.renderStatsChart(props as StatsChartProps));
        break;
      case 'blog-magazine':
        wrapper.appendChild(this.renderBlogMagazine(props as BlogMagazineProps));
        break;
      case 'sales-dashboard':
        wrapper.appendChild(this.renderSalesDashboard(props as SalesDashboardProps));
        break;
      default:
        wrapper.appendChild(this.renderFallback(props));
    }

    // Tier badge removed - was showing debug info like "Registry Template" to users

    this.container.appendChild(wrapper);
  }

  /**
   * Clear the rendered content
   */
  clear(): void {
    this.container.innerHTML = '';
  }

  // ==================== Template Renderers ====================

  private renderTemplateGrid(props: TemplateGridProps): HTMLElement {
    const grid = document.createElement('div');
    grid.className = 'a2ui-template-grid';

    const header = document.createElement('div');
    header.className = 'a2ui-grid-header';
    header.innerHTML = `
      <h3 class="a2ui-grid-title">${this.escapeHtml(props.title)}</h3>
      ${props.showCount ? `<span class="a2ui-grid-count">${props.templates?.length || 0} items</span>` : ''}
    `;
    grid.appendChild(header);

    const items = document.createElement('div');
    items.className = 'a2ui-grid-items';

    (props.templates || []).forEach((item, idx) => {
      const card = document.createElement('div');
      card.className = 'a2ui-grid-item';
      card.style.animationDelay = `${idx * 0.1}s`;

      card.innerHTML = `
        <div class="a2ui-item-header">
          <h4 class="a2ui-item-name">${this.escapeHtml(item.name)}</h4>
          ${item.category ? `<span class="a2ui-item-category">${this.escapeHtml(item.category)}</span>` : ''}
        </div>
        <p class="a2ui-item-description">${this.escapeHtml(item.description)}</p>
      `;

      items.appendChild(card);
    });

    grid.appendChild(items);
    return grid;
  }

  private renderTimeline(props: TimelineProps): HTMLElement {
    const timeline = document.createElement('div');
    timeline.className = 'a2ui-timeline';

    const header = document.createElement('h3');
    header.className = 'a2ui-timeline-title';
    header.textContent = props.title;
    timeline.appendChild(header);

    const events = document.createElement('div');
    events.className = 'a2ui-timeline-events';

    (props.events || []).forEach((event, idx) => {
      const item = document.createElement('div');
      item.className = 'a2ui-timeline-event';
      item.style.animationDelay = `${idx * 0.15}s`;

      item.innerHTML = `
        <div class="a2ui-event-marker">
          <span class="a2ui-event-year">${this.escapeHtml(event.year)}</span>
        </div>
        <div class="a2ui-event-content">
          <h4 class="a2ui-event-title">${this.escapeHtml(event.title)}</h4>
          <p class="a2ui-event-description">${this.escapeHtml(event.description)}</p>
        </div>
      `;

      events.appendChild(item);
    });

    timeline.appendChild(events);
    return timeline;
  }

  private renderContactCard(props: ContactCardProps): HTMLElement {
    const card = document.createElement('div');
    card.className = 'a2ui-contact-card';

    const header = document.createElement('h3');
    header.className = 'a2ui-contact-title';
    header.textContent = props.title;
    card.appendChild(header);

    const contacts = document.createElement('div');
    contacts.className = 'a2ui-contact-items';

    (props.contacts || []).forEach((contact) => {
      const item = document.createElement('div');
      item.className = 'a2ui-contact-item';

      const icon = this.getContactIcon(contact.type);
      item.innerHTML = `
        <span class="a2ui-contact-icon">${icon}</span>
        <div class="a2ui-contact-info">
          <span class="a2ui-contact-value">${this.escapeHtml(contact.value)}</span>
          ${contact.description ? `<span class="a2ui-contact-desc">${this.escapeHtml(contact.description)}</span>` : ''}
        </div>
      `;

      contacts.appendChild(item);
    });

    card.appendChild(contacts);
    return card;
  }

  private renderComparisonChart(props: ComparisonChartProps): HTMLElement {
    const chart = document.createElement('div');
    chart.className = 'a2ui-comparison-chart';

    const header = document.createElement('h3');
    header.className = 'a2ui-comparison-title';
    header.textContent = props.title;
    chart.appendChild(header);

    const table = document.createElement('div');
    table.className = 'a2ui-comparison-table';

    (props.items || []).forEach((item) => {
      const column = document.createElement('div');
      column.className = 'a2ui-comparison-column';
      if (item.recommended) column.classList.add('a2ui-recommended');

      let featuresHtml = '';
      (item.features || []).forEach((f) => {
        featuresHtml += `
          <div class="a2ui-comparison-row">
            <span class="a2ui-feature-name">${this.escapeHtml(f.feature)}</span>
            <span class="a2ui-feature-value">${this.escapeHtml(f.value)}</span>
          </div>
        `;
      });

      column.innerHTML = `
        <div class="a2ui-comparison-header">
          <h4>${this.escapeHtml(item.name)}</h4>
          ${item.recommended ? '<span class="a2ui-badge">Recommended</span>' : ''}
        </div>
        <div class="a2ui-comparison-features">${featuresHtml}</div>
      `;

      table.appendChild(column);
    });

    chart.appendChild(table);
    return chart;
  }

  private renderStatsFlowLayout(props: StatsFlowLayoutProps): HTMLElement {
    const layout = document.createElement('div');
    layout.className = 'a2ui-stats-flow';

    const header = document.createElement('h3');
    header.className = 'a2ui-stats-title';
    header.textContent = props.title;
    layout.appendChild(header);

    // Top stats
    if (props.topStats?.length) {
      const topSection = document.createElement('div');
      topSection.className = 'a2ui-stats-row a2ui-stats-top';

      props.topStats.forEach((stat) => {
        const statCard = document.createElement('div');
        statCard.className = 'a2ui-stat-card';
        statCard.innerHTML = `
          <span class="a2ui-stat-value">${this.escapeHtml(stat.value)}</span>
          <span class="a2ui-stat-label">${this.escapeHtml(stat.label)}</span>
        `;
        topSection.appendChild(statCard);
      });

      layout.appendChild(topSection);
    }

    // Bottom stats
    if (props.bottomStats?.length) {
      const bottomSection = document.createElement('div');
      bottomSection.className = 'a2ui-stats-row a2ui-stats-bottom';

      props.bottomStats.forEach((stat) => {
        const statCard = document.createElement('div');
        statCard.className = 'a2ui-stat-card';
        statCard.innerHTML = `
          <span class="a2ui-stat-value">${this.escapeHtml(stat.value)}</span>
          <span class="a2ui-stat-label">${this.escapeHtml(stat.label)}</span>
        `;
        bottomSection.appendChild(statCard);
      });

      layout.appendChild(bottomSection);
    }

    return layout;
  }

  private renderTeamFlipCards(props: TeamFlipCardsProps): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-team-cards';

    const header = document.createElement('h3');
    header.className = 'a2ui-team-title';
    header.textContent = props.title;
    container.appendChild(header);

    const cards = document.createElement('div');
    cards.className = 'a2ui-team-grid';

    // Dynamic column count based on number of members (max 4 columns)
    const memberCount = props.members?.length || 0;
    const columnCount = Math.min(memberCount, 4);
    cards.style.gridTemplateColumns = `repeat(${columnCount}, minmax(0, 1fr))`;

    (props.members || []).forEach((member) => {
      const card = document.createElement('div');
      card.className = 'a2ui-team-card';

      // Get initials (first letter of first name + first letter of last name)
      const nameParts = member.name.trim().split(/\s+/);
      const initials = nameParts.length >= 2
        ? (nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)).toUpperCase()
        : member.name.substring(0, 2).toUpperCase();

      card.innerHTML = `
        <div class="a2ui-team-front">
          <div class="a2ui-team-avatar">${initials}</div>
          <h4 class="a2ui-team-name">${this.escapeHtml(member.name)}</h4>
          <span class="a2ui-team-role">${this.escapeHtml(member.role)}</span>
        </div>
        <div class="a2ui-team-back">
          <p class="a2ui-team-bio">${this.escapeHtml(member.bio || '')}</p>
        </div>
      `;

      // Add flip interaction
      card.addEventListener('click', () => {
        card.classList.toggle('flipped');
      });

      cards.appendChild(card);
    });

    container.appendChild(cards);
    return container;
  }

  private renderServiceHoverReveal(props: ServiceHoverRevealProps): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-services';

    const header = document.createElement('h3');
    header.className = 'a2ui-services-title';
    header.textContent = props.title;
    container.appendChild(header);

    const list = document.createElement('div');
    list.className = 'a2ui-services-list';

    (props.services || []).forEach((service, idx) => {
      const item = document.createElement('div');
      item.className = 'a2ui-service-item';

      item.innerHTML = `
        <div class="a2ui-service-header">
          <span class="a2ui-service-number">${String(idx + 1).padStart(2, '0')}</span>
          <h4 class="a2ui-service-name">${this.escapeHtml(service.name)}</h4>
          <span class="a2ui-service-arrow">→</span>
        </div>
        <div class="a2ui-service-reveal">
          <p>${this.escapeHtml(service.description)}</p>
          ${service.fullDescription ? `<p class="a2ui-service-full">${this.escapeHtml(service.fullDescription)}</p>` : ''}
        </div>
      `;

      list.appendChild(item);
    });

    container.appendChild(list);
    return container;
  }

  private renderMagazineHero(props: MagazineHeroProps): HTMLElement {
    const hero = document.createElement('div');
    hero.className = 'a2ui-magazine-hero';

    const hasInfoCards = props.projectInfo || props.services?.length;

    hero.innerHTML = `
      <div class="a2ui-hero-header">
        <h2 class="a2ui-hero-title">${this.escapeHtml(props.title)}</h2>
        <p class="a2ui-hero-description">${this.escapeHtml(props.content)}</p>
      </div>

      ${hasInfoCards ? `
        <div class="a2ui-hero-layout">
          <div class="a2ui-hero-media">
            ${props.image ? `<img src="${this.escapeHtml(props.image)}" alt="" class="a2ui-hero-image" />` : ''}
          </div>
          <div class="a2ui-hero-info-cards">
            ${props.projectInfo ? `
              <div class="a2ui-hero-info-card">
                <h4 class="a2ui-hero-info-title">Project Info</h4>
                <div class="a2ui-hero-info-list">
                  ${props.projectInfo.year ? `<div class="a2ui-hero-info-item">Year: ${this.escapeHtml(props.projectInfo.year)}</div>` : ''}
                  ${props.projectInfo.team ? `<div class="a2ui-hero-info-item">${this.escapeHtml(props.projectInfo.team)}</div>` : ''}
                  ${props.projectInfo.duration ? `<div class="a2ui-hero-info-item">${this.escapeHtml(props.projectInfo.duration)}</div>` : ''}
                </div>
              </div>
            ` : ''}
            ${props.services?.length ? `
              <div class="a2ui-hero-info-card">
                <h4 class="a2ui-hero-info-title">Services</h4>
                <div class="a2ui-hero-info-list">
                  ${props.services.map(service => `<div class="a2ui-hero-info-item">${this.escapeHtml(service)}</div>`).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      ` : `
        <div class="a2ui-hero-content">
          ${props.subtitle ? `<p class="a2ui-hero-subtitle">${this.escapeHtml(props.subtitle)}</p>` : ''}
        </div>
      `}

      ${props.pullQuote ? `<blockquote class="a2ui-hero-quote">"${this.escapeHtml(props.pullQuote)}"</blockquote>` : ''}

      ${props.tags?.length ? `
        <div class="a2ui-hero-tags">
          ${props.tags.map(tag => `<span class="a2ui-tag">${this.escapeHtml(tag)}</span>`).join('')}
        </div>
      ` : ''}
    `;

    return hero;
  }

  private renderFAQAccordion(props: FAQAccordionProps): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-faq-accordion';

    const header = document.createElement('h3');
    header.className = 'a2ui-faq-title';
    header.textContent = props.title;
    container.appendChild(header);

    const list = document.createElement('div');
    list.className = 'a2ui-faq-list';

    (props.faqs || []).forEach((faq, idx) => {
      const item = document.createElement('div');
      item.className = 'a2ui-faq-item';
      if (idx === 0) item.classList.add('open');

      item.innerHTML = `
        <div class="a2ui-faq-question">
          <span>${this.escapeHtml(faq.question)}</span>
          <span class="a2ui-faq-icon">+</span>
        </div>
        <div class="a2ui-faq-answer">
          <p>${this.escapeHtml(faq.answer)}</p>
        </div>
      `;

      // Toggle accordion
      const questionEl = item.querySelector('.a2ui-faq-question');
      questionEl?.addEventListener('click', () => {
        item.classList.toggle('open');
      });

      list.appendChild(item);
    });

    container.appendChild(list);
    return container;
  }

  private renderImageGallery(props: ImageGalleryProps): HTMLElement {
    const gallery = document.createElement('div');
    gallery.className = 'a2ui-image-gallery';

    const header = document.createElement('h3');
    header.className = 'a2ui-gallery-title';
    header.textContent = props.title;
    gallery.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'a2ui-gallery-grid';

    (props.images || []).forEach((img) => {
      const item = document.createElement('div');
      item.className = 'a2ui-gallery-item';

      item.innerHTML = `
        <img src="${this.escapeHtml(img.url)}" alt="${this.escapeHtml(img.alt || '')}" loading="lazy" />
        ${img.caption ? `<span class="a2ui-gallery-caption">${this.escapeHtml(img.caption)}</span>` : ''}
      `;

      grid.appendChild(item);
    });

    gallery.appendChild(grid);
    return gallery;
  }

  private renderVideoGallery(props: VideoGalleryProps): HTMLElement {
    const gallery = document.createElement('div');
    gallery.className = 'a2ui-video-gallery';

    const header = document.createElement('h3');
    header.className = 'a2ui-gallery-title';
    header.textContent = props.title;
    gallery.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'a2ui-video-grid';

    (props.videos || []).forEach((video) => {
      const item = document.createElement('div');
      item.className = 'a2ui-video-item';

      // Check if YouTube URL
      const youtubeId = this.extractYouTubeId(video.url);

      if (youtubeId) {
        item.innerHTML = `
          <div class="a2ui-video-embed">
            <iframe src="https://www.youtube.com/embed/${youtubeId}"
                    frameborder="0" allowfullscreen loading="lazy"></iframe>
          </div>
          <h4 class="a2ui-video-title">${this.escapeHtml(video.title)}</h4>
        `;
      } else {
        item.innerHTML = `
          <video controls>
            <source src="${this.escapeHtml(video.url)}" type="video/mp4">
          </video>
          <h4 class="a2ui-video-title">${this.escapeHtml(video.title)}</h4>
        `;
      }

      grid.appendChild(item);
    });

    gallery.appendChild(grid);
    return gallery;
  }

  private renderStatsChart(props: StatsChartProps): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-stats-chart';

    // Title
    if (props.title) {
      const header = document.createElement('div');
      header.className = 'a2ui-stats-chart-header';
      header.innerHTML = `
        <span class="a2ui-stats-chart-icon">📊</span>
        <h2 class="a2ui-stats-chart-title">${this.escapeHtml(props.title)}</h2>
      `;
      container.appendChild(header);
    }

    // Metrics as horizontal bars
    const metrics = (props as any).metrics || props.stats || [];
    if (Array.isArray(metrics) && metrics.length > 0) {
      const metricsContainer = document.createElement('div');
      metricsContainer.className = 'a2ui-stats-chart-metrics';

      // Calculate max value for bar visualization
      const numericMetrics = metrics.filter((m: any) => !isNaN(parseFloat(m.value)));
      const maxValue = numericMetrics.length > 0
        ? Math.max(...numericMetrics.map((m: any) => parseFloat(m.value)))
        : 100;

      metrics.forEach((metric: any) => {
        const value = metric.value;
        const numericValue = parseFloat(value);
        const isNumeric = !isNaN(numericValue);
        const percentage = isNumeric ? (numericValue / maxValue) * 100 : 0;

        const metricEl = document.createElement('div');
        metricEl.className = 'a2ui-stats-chart-metric';

        metricEl.innerHTML = `
          <div class="a2ui-stats-chart-metric-header">
            <div class="a2ui-stats-chart-metric-label">${this.escapeHtml(metric.label || metric.name || 'Metric')}</div>
            <div class="a2ui-stats-chart-metric-value">${this.escapeHtml(String(value))}</div>
          </div>
          ${isNumeric ? `
            <div class="a2ui-stats-chart-bar-container">
              <div class="a2ui-stats-chart-bar" style="width: ${Math.min(percentage, 100)}%"></div>
            </div>
          ` : ''}
        `;

        metricsContainer.appendChild(metricEl);
      });

      container.appendChild(metricsContainer);
    }

    return container;
  }

  private renderBlogMagazine(props: BlogMagazineProps): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-blog-magazine';

    // Title with red accent
    if (props.title) {
      const header = document.createElement('div');
      header.className = 'a2ui-blog-magazine-header';
      header.innerHTML = `
        <div class="a2ui-blog-magazine-accent"></div>
        <h2 class="a2ui-blog-magazine-title">${this.escapeHtml(props.title)}</h2>
      `;
      container.appendChild(header);
    }

    const posts = props.posts || [];
    if (posts.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'a2ui-blog-magazine-empty';
      empty.textContent = 'No blog posts available.';
      container.appendChild(empty);
      return container;
    }

    // Magazine layout with sidebar
    const layout = document.createElement('div');
    layout.className = 'a2ui-blog-magazine-layout';

    // Main content area
    const mainContent = document.createElement('div');
    mainContent.className = 'a2ui-blog-magazine-main';

    // Featured post (first post with featured flag or first post)
    const featuredPost = posts.find((p: any) => p.featured) || posts[0];
    const otherPosts = posts.filter((p: any) => p !== featuredPost);

    if (featuredPost) {
      const featured = document.createElement('div');
      featured.className = 'a2ui-blog-magazine-featured';
      featured.innerHTML = `
        <div class="a2ui-blog-magazine-featured-content">
          <div class="a2ui-blog-magazine-featured-image">
            <span class="a2ui-blog-magazine-featured-number">01</span>
          </div>
          <div class="a2ui-blog-magazine-featured-info">
            <span class="a2ui-blog-magazine-category">${this.escapeHtml(featuredPost.category || 'General')}</span>
            <h3 class="a2ui-blog-magazine-featured-title">${this.escapeHtml(featuredPost.title)}</h3>
            <p class="a2ui-blog-magazine-excerpt">${this.escapeHtml(featuredPost.excerpt || '')}</p>
            <div class="a2ui-blog-magazine-meta">
              ${featuredPost.author ? `<span class="a2ui-blog-magazine-author">👤 ${this.escapeHtml(featuredPost.author)}</span>` : ''}
              ${featuredPost.date ? `<span class="a2ui-blog-magazine-date">📅 ${this.escapeHtml(featuredPost.date)}</span>` : ''}
              ${featuredPost.readTime ? `<span class="a2ui-blog-magazine-read-time">⏱️ ${this.escapeHtml(featuredPost.readTime)}</span>` : ''}
            </div>
          </div>
        </div>
      `;
      mainContent.appendChild(featured);
    }

    // Other posts
    otherPosts.forEach((post: any, index: number) => {
      const article = document.createElement('article');
      article.className = 'a2ui-blog-magazine-post';
      article.innerHTML = `
        <div class="a2ui-blog-magazine-post-number">
          <span>0${index + 2}</span>
        </div>
        <div class="a2ui-blog-magazine-post-content">
          <span class="a2ui-blog-magazine-category">${this.escapeHtml(post.category || 'General')}</span>
          <h3 class="a2ui-blog-magazine-post-title">${this.escapeHtml(post.title)}</h3>
          <p class="a2ui-blog-magazine-excerpt">${this.escapeHtml(post.excerpt || '')}</p>
          <div class="a2ui-blog-magazine-meta">
            ${post.author ? `<span class="a2ui-blog-magazine-author">👤 ${this.escapeHtml(post.author)}</span>` : ''}
            ${post.date ? `<span class="a2ui-blog-magazine-date">${this.escapeHtml(post.date)}</span>` : ''}
          </div>
        </div>
      `;
      mainContent.appendChild(article);
    });

    layout.appendChild(mainContent);

    // Sidebar
    const sidebar = document.createElement('aside');
    sidebar.className = 'a2ui-blog-magazine-sidebar';

    // Categories
    const categories = ['All', ...new Set(posts.map((p: any) => p.category || 'General'))];
    const categoriesBox = document.createElement('div');
    categoriesBox.className = 'a2ui-blog-magazine-categories';
    categoriesBox.innerHTML = `
      <h3 class="a2ui-blog-magazine-sidebar-title">Categories</h3>
      <div class="a2ui-blog-magazine-category-list">
        ${categories.map(cat => `<button class="a2ui-blog-magazine-category-btn">${this.escapeHtml(String(cat))}</button>`).join('')}
      </div>
    `;
    sidebar.appendChild(categoriesBox);

    // Newsletter CTA
    const newsletter = document.createElement('div');
    newsletter.className = 'a2ui-blog-magazine-newsletter';
    newsletter.innerHTML = `
      <h3 class="a2ui-blog-magazine-newsletter-title">Newsletter</h3>
      <p class="a2ui-blog-magazine-newsletter-text">Get the latest articles delivered to your inbox.</p>
      <input type="email" placeholder="your@email.com" class="a2ui-blog-magazine-newsletter-input" />
      <button class="a2ui-blog-magazine-newsletter-btn">Subscribe</button>
    `;
    sidebar.appendChild(newsletter);

    layout.appendChild(sidebar);
    container.appendChild(layout);

    return container;
  }

  private renderSalesDashboard(props: SalesDashboardProps): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-sales-dashboard';

    // Header
    if (props.title) {
      const header = document.createElement('div');
      header.className = 'a2ui-sales-dashboard-header';
      header.innerHTML = `
        <h2 class="a2ui-sales-dashboard-title">${this.escapeHtml(props.title)}</h2>
        ${props.subtitle ? `<p class="a2ui-sales-dashboard-subtitle">${this.escapeHtml(props.subtitle)}</p>` : ''}
      `;
      container.appendChild(header);
    }

    // KPI Cards
    const kpiCards = props.kpiCards || [];
    if (kpiCards.length > 0) {
      const kpiGrid = document.createElement('div');
      kpiGrid.className = 'a2ui-sales-dashboard-kpi-grid';

      kpiCards.forEach((kpi: any) => {
        const card = document.createElement('div');
        card.className = `a2ui-sales-dashboard-kpi-card ${kpi.variant ? `a2ui-kpi-${kpi.variant}` : ''}`;

        const trendHtml = kpi.trend ? `
          <div class="a2ui-sales-dashboard-kpi-trend ${kpi.trend.isPositive ? 'positive' : 'negative'}">
            ${kpi.trend.isPositive ? '↑' : '↓'} ${kpi.trend.value}%
          </div>
        ` : '';

        card.innerHTML = `
          <div class="a2ui-sales-dashboard-kpi-header">
            ${kpi.icon ? `<span class="a2ui-sales-dashboard-kpi-icon">${this.escapeHtml(kpi.icon)}</span>` : ''}
            ${trendHtml}
          </div>
          <div class="a2ui-sales-dashboard-kpi-value">${this.escapeHtml(kpi.value)}</div>
          <div class="a2ui-sales-dashboard-kpi-title">${this.escapeHtml(kpi.title)}</div>
          ${kpi.subtitle ? `<div class="a2ui-sales-dashboard-kpi-subtitle">${this.escapeHtml(kpi.subtitle)}</div>` : ''}
        `;

        kpiGrid.appendChild(card);
      });

      container.appendChild(kpiGrid);
    }

    // Charts
    const charts = props.charts || [];
    if (charts.length > 0) {
      const chartsGrid = document.createElement('div');
      chartsGrid.className = 'a2ui-sales-dashboard-charts-grid';

      charts.forEach((chart: any) => {
        const chartCard = document.createElement('div');
        chartCard.className = 'a2ui-sales-dashboard-chart-card';

        let chartContent = '';
        const data = Array.isArray(chart.data) ? chart.data : [];

        if (chart.type === 'bar' || chart.type === 'line') {
          // Simple bar visualization
          const maxValue = data.length > 0 ? Math.max(...data.map((d: any) => d.value || 0)) : 100;
          chartContent = `
            <div class="a2ui-sales-dashboard-chart-bars">
              ${data.map((d: any) => `
                <div class="a2ui-sales-dashboard-chart-bar-item">
                  <div class="a2ui-sales-dashboard-chart-bar" style="height: ${((d.value || 0) / maxValue) * 100}%"></div>
                  <span class="a2ui-sales-dashboard-chart-bar-label">${this.escapeHtml(d.name || '')}</span>
                </div>
              `).join('')}
            </div>
          `;
        } else if (chart.type === 'pie') {
          // Simple pie representation as list
          const total = data.reduce((sum: number, d: any) => sum + (d.value || 0), 0);
          chartContent = `
            <div class="a2ui-sales-dashboard-chart-pie-list">
              ${data.map((d: any) => `
                <div class="a2ui-sales-dashboard-chart-pie-item">
                  <span class="a2ui-sales-dashboard-chart-pie-name">${this.escapeHtml(d.name || '')}</span>
                  <span class="a2ui-sales-dashboard-chart-pie-value">${total > 0 ? Math.round(((d.value || 0) / total) * 100) : 0}%</span>
                </div>
              `).join('')}
            </div>
          `;
        } else {
          // Table fallback
          chartContent = `
            <div class="a2ui-sales-dashboard-chart-table">
              ${data.map((d: any) => `
                <div class="a2ui-sales-dashboard-chart-table-row">
                  <span>${this.escapeHtml(d.name || '')}</span>
                  <span>${this.escapeHtml(String(d.value || ''))}</span>
                </div>
              `).join('')}
            </div>
          `;
        }

        chartCard.innerHTML = `
          <div class="a2ui-sales-dashboard-chart-header">
            <h3 class="a2ui-sales-dashboard-chart-title">${this.escapeHtml(chart.title)}</h3>
            ${chart.subtitle ? `<p class="a2ui-sales-dashboard-chart-subtitle">${this.escapeHtml(chart.subtitle)}</p>` : ''}
          </div>
          ${chartContent}
        `;

        chartsGrid.appendChild(chartCard);
      });

      container.appendChild(chartsGrid);
    }

    return container;
  }

  private renderFallback(props: any): HTMLElement {
    // Use magazine-hero style as fallback
    const hero = document.createElement('div');
    hero.className = 'a2ui-magazine-hero a2ui-fallback';

    const title = props.title || 'Information';
    const content = props.content || props.description || (typeof props === 'string' ? props : '');
    const subtitle = props.subtitle || '';

    hero.innerHTML = `
      <div class="a2ui-hero-header">
        <div class="a2ui-hero-accent"></div>
        <h2 class="a2ui-hero-title">${this.escapeHtml(title)}</h2>
        ${subtitle ? `<p class="a2ui-hero-subtitle">${this.escapeHtml(subtitle)}</p>` : ''}
      </div>
      ${content ? `
        <div class="a2ui-hero-content">
          <p>${this.escapeHtml(content)}</p>
        </div>
      ` : ''}
      ${props.tags?.length ? `
        <div class="a2ui-hero-tags">
          ${props.tags.map((tag: string) => `<span class="a2ui-tag">${this.escapeHtml(tag)}</span>`).join('')}
        </div>
      ` : ''}
    `;

    return hero;
  }

  // ==================== Helper Methods ====================

  private escapeHtml(text: string): string {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private getIcon(name: string): string {
    const icons: Record<string, string> = {
      info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
      check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
      star: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
    };
    return icons[name] || icons.info;
  }

  private getContactIcon(type: string): string {
    const icons: Record<string, string> = {
      email: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><path d="M22 6l-10 7L2 6"/></svg>',
      phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>',
      address: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>',
      website: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>',
      info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    };
    return icons[type] || icons.info;
  }

  private extractYouTubeId(url: string): string | null {
    const match = url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/);
    return match ? match[1] : null;
  }
}

// Export singleton factory
let _rendererInstance: A2UIRenderer | null = null;

export function getA2UIRenderer(containerId: string = 'a2ui-container'): A2UIRenderer {
  if (!_rendererInstance) {
    _rendererInstance = new A2UIRenderer(containerId);
  }
  return _rendererInstance;
}
