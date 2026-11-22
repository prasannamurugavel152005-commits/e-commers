import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowRight,
  BadgeCheck,
  Camera,
  Check,
  ChevronDown,
  ChevronRight,
  CirclePlay,
  Headset,
  Heart,
  LockKeyhole,
  Mail,
  MapPin,
  Menu,
  Minus,
  PackageCheck,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Smartphone,
  ShoppingCart,
  SlidersHorizontal,
  Sparkles,
  Star,
  Truck,
  UserRound,
  UsersRound,
  X,
} from 'lucide-react'
import logoImage from './assets/pexo-market-logo.png'
import api, { authStorage } from './api/client'
import './App.css'

const defaultCategories = ['All', 'Electronics', 'Home', 'Fashion', 'Kitchen']
const imageUrl = (id, width = 560) =>
  `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${width}&q=85`
const money = (amount) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim() || ''

function GoogleSignInButton({ onCredential, onUnavailable }) {
  const buttonRef = useRef(null)
  const callbacksRef = useRef({ onCredential, onUnavailable })

  useEffect(() => {
    callbacksRef.current = { onCredential, onUnavailable }
  }, [onCredential, onUnavailable])

  useEffect(() => {
    if (!googleClientId) return undefined

    let active = true
    const buttonContainer = buttonRef.current
    const renderGoogleButton = () => {
      const googleIdentity = window.google?.accounts?.id
      if (!active || !googleIdentity || !buttonContainer) return

      googleIdentity.initialize({
        client_id: googleClientId,
        callback: (response) => {
          if (response?.credential) {
            callbacksRef.current.onCredential(response.credential)
          } else {
            callbacksRef.current.onUnavailable(
              'Google did not return a sign-in credential. Please try again.',
            )
          }
        },
      })
      googleIdentity.renderButton(buttonContainer, {
        theme: 'outline',
        size: 'large',
        text: 'continue_with',
        shape: 'rectangular',
        logo_alignment: 'left',
        width: Math.min(360, buttonContainer.clientWidth || 320),
      })
    }
    const handleScriptError = () => {
      callbacksRef.current.onUnavailable(
        'Google sign-in could not load. Please try email and password.',
      )
    }

    let script = document.querySelector('script[data-google-identity]')
    if (!script) {
      script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.dataset.googleIdentity = 'true'
      document.head.appendChild(script)
    }

    if (window.google?.accounts?.id) {
      renderGoogleButton()
    } else {
      script.addEventListener('load', renderGoogleButton)
    }
    script.addEventListener('error', handleScriptError)

    return () => {
      active = false
      script.removeEventListener('load', renderGoogleButton)
      script.removeEventListener('error', handleScriptError)
      buttonContainer?.replaceChildren()
    }
  }, [])

  if (!googleClientId) {
    return (
      <button
        className="google-signin-button"
        onClick={() => onUnavailable(
          'Google sign-in is not configured yet. Add the Google client ID to enable it.',
        )}
        type="button"
      >
        <span className="google-mark" aria-hidden="true">G</span>
        Continue with Google
      </button>
    )
  }

  return <div className="google-signin-container" ref={buttonRef} />
}

function AuthPage({ initialMode, onClose, onAuthenticated }) {
  const [mode, setMode] = useState(initialMode)
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    passwordConfirm: '',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const updateForm = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const endpoint =
        mode === 'register' ? '/accounts/register/' : '/accounts/login/'
      const payload = {
        email: form.email,
        password: form.password,
      }

      if (mode === 'register') {
        const [firstName, ...lastName] = form.name.trim().split(/\s+/)
        payload.first_name = firstName
        payload.last_name = lastName.join(' ')
        payload.password_confirm = form.passwordConfirm
      }

      const { data } = await api.post(endpoint, payload)
      authStorage.save(data)
      onAuthenticated(data.user)
    } catch (requestError) {
      const responseData = requestError.response?.data
      const message = responseData
        ? Object.values(responseData).flat()[0]
        : 'Could not reach the shop. Check that the backend is running.'
      setError(typeof message === 'string' ? message : 'Please check the form and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleGoogleCredential = async (credential) => {
    setError('')
    setSubmitting(true)
    try {
      const { data } = await api.post('/accounts/google/', { credential })
      authStorage.save(data)
      onAuthenticated(data.user)
    } catch (requestError) {
      const message =
        requestError.response?.data?.detail ||
        'Could not complete Google sign-in. Please try again.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page" role="presentation">
      <button className="auth-close" type="button" onClick={onClose} aria-label="Close sign in">
        <X size={21} />
      </button>
      <div className="auth-promo">
        <img src={logoImage} alt="Pexo Market" />
        <span className="section-kicker">A BETTER KIND OF EVERYDAY</span>
        <h1>Good finds.<br /><em>Good to have you.</em></h1>
        <p>Sign in to keep your favorite finds close and make checkout a little easier.</p>
        <div className="auth-promo-note"><ShieldCheck size={17} /> Your account stays yours. Always.</div>
      </div>
      <div className="auth-form-wrap">
        <div className="auth-form-card">
          <span className="section-kicker">{mode === 'login' ? 'WELCOME BACK' : 'JOIN THE GOOD FINDS'}</span>
          <h2>{mode === 'login' ? 'Sign in to Pexo' : 'Create your account'}</h2>
          <p className="auth-intro">
            {mode === 'login'
              ? 'Your next favorite thing is just around the corner.'
              : 'A few details and you’re ready to discover.'}
          </p>
          <form onSubmit={handleSubmit}>
            {mode === 'register' && (
              <label>
                Your name
                <input
                  autoComplete="name"
                  name="name"
                  onChange={updateForm}
                  placeholder="First and last name"
                  required
                  value={form.name}
                />
              </label>
            )}
            <label>
              Email address
              <input
                autoComplete="email"
                name="email"
                onChange={updateForm}
                placeholder="you@example.com"
                required
                type="email"
                value={form.email}
              />
            </label>
            <label>
              Password
              <input
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={8}
                name="password"
                onChange={updateForm}
                placeholder="At least 8 characters"
                required
                type="password"
                value={form.password}
              />
            </label>
            {mode === 'register' && (
              <label>
                Confirm password
                <input
                  autoComplete="new-password"
                  minLength={8}
                  name="passwordConfirm"
                  onChange={updateForm}
                  placeholder="Type your password again"
                  required
                  type="password"
                  value={form.passwordConfirm}
                />
              </label>
            )}
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="auth-submit" disabled={submitting} type="submit">
              {submitting
                ? 'One moment...'
                : mode === 'login'
                  ? 'Sign in'
                  : 'Create account'}
              {!submitting && <ArrowRight size={17} />}
            </button>
          </form>
          <div className="auth-divider"><span>or continue with</span></div>
          <GoogleSignInButton
            onCredential={handleGoogleCredential}
            onUnavailable={setError}
          />
          {!googleClientId && (
            <p className="google-config-note">
              Google sign-in becomes available after OAuth is configured.
            </p>
          )}
          <p className="auth-switch">
            {mode === 'login' ? 'New to Pexo?' : 'Already have an account?'}
            <button
              type="button"
              onClick={() => {
                setError('')
                setMode(mode === 'login' ? 'register' : 'login')
              }}
            >
              {mode === 'login' ? 'Create an account' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState(defaultCategories)
  const [productsLoading, setProductsLoading] = useState(true)
  const [productError, setProductError] = useState('')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [sort, setSort] = useState('featured')
  const [cart, setCart] = useState({})
  const [favorites, setFavorites] = useState([])
  const [cartOpen, setCartOpen] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [authMode, setAuthMode] = useState(null)
  const [authUser, setAuthUser] = useState(null)

  useEffect(() => {
    let active = true
    api.get('/products/')
      .then(({ data }) => {
        if (!active) return
        const rows = Array.isArray(data) ? data : data.results
        setProducts(rows.map((product) => ({
          ...product,
          oldPrice: product.oldPrice ?? product.compare_at_price,
          reviews: product.reviews ?? product.review_count ?? 0,
          image: product.image ?? product.image_url,
          imageAttribution: product.image_attribution ?? '',
          imageSourceUrl: product.image_source_url ?? '',
          imageLicense: product.image_license ?? '',
          imageLicenseUrl: product.image_license_url ?? '',
          color: ['sand', 'blue', 'peach', 'lavender', 'mint', 'pink', 'cream', 'lilac'][product.id % 8],
        })))
        setProductsLoading(false)
      })
      .catch(() => {
        if (!active) return
        setProductError('We could not load the catalog. Check that the backend is running.')
        setProductsLoading(false)
      })

    api.get('/products/categories/')
      .then(({ data }) => {
        const rows = Array.isArray(data) ? data : data.results
        if (active && Array.isArray(rows)) {
          setCategories(['All', ...rows.map((item) => item.name)])
        }
      })
      .catch(() => {
        if (active) setProductError('We could not load shop categories from the backend.')
      })

    const savedAccess = localStorage.getItem('pexo_access')
    if (savedAccess) {
      api.get('/accounts/profile/')
        .then(({ data }) => {
          if (active) setAuthUser(data)
        })
        .catch(() => {
          if (!active) return
          authStorage.clear()
          setAuthUser(null)
        })
    }

    const clearSession = () => setAuthUser(null)
    window.addEventListener('pexo:session-expired', clearSession)
    return () => {
      active = false
      window.removeEventListener('pexo:session-expired', clearSession)
    }
  }, [])

  const visibleProducts = useMemo(() => {
    const searchTerm = query.trim().toLowerCase()
    const filtered = products.filter((product) => {
      const matchesCategory =
        category === 'All' || product.category === category
      const matchesQuery =
        !searchTerm ||
        `${product.name} ${product.detail} ${product.category}`
          .toLowerCase()
          .includes(searchTerm)
      return matchesCategory && matchesQuery
    })

    if (sort === 'price-low') {
      return filtered.sort((a, b) => a.price - b.price)
    }
    if (sort === 'price-high') {
      return filtered.sort((a, b) => b.price - a.price)
    }
    if (sort === 'rating') {
      return filtered.sort((a, b) => b.rating - a.rating)
    }
    return filtered
  }, [category, products, query, sort])

  const cartItems = products.filter((product) => cart[product.id])
  const cartCount = Object.values(cart).reduce((total, count) => total + count, 0)
  const subtotal = cartItems.reduce(
    (total, product) => total + product.price * cart[product.id],
    0,
  )

  const addToCart = (productId) => {
    setCart((current) => ({
      ...current,
      [productId]: (current[productId] || 0) + 1,
    }))
  }

  const changeQuantity = (productId, amount) => {
    setCart((current) => {
      const nextQuantity = (current[productId] || 0) + amount
      if (nextQuantity <= 0) {
        const nextCart = { ...current }
        delete nextCart[productId]
        return nextCart
      }
      return { ...current, [productId]: nextQuantity }
    })
  }

  const toggleFavorite = (productId) => {
    setFavorites((current) =>
      current.includes(productId)
        ? current.filter((id) => id !== productId)
        : [...current, productId],
    )
  }

  const showCategory = (nextCategory) => {
    setCategory(nextCategory)
    setMobileNavOpen(false)
    document.getElementById('shop')?.scrollIntoView({ behavior: 'smooth' })
  }

  const signOut = () => {
    authStorage.clear()
    setAuthUser(null)
  }

  return (
    <div className="storefront">
      <div className="announcement">
        <Sparkles size={14} aria-hidden="true" />
        <span>Small finds. Big happy.</span>
        <span className="announcement-divider">|</span>
        <span>Free delivery on orders over ₹999</span>
      </div>

      <header className="site-header">
        <a className="brand" href="#" aria-label="Pexo Market home">
          <img className="brand-logo" src={logoImage} alt="Pexo Market" />
        </a>

        <button className="location-button" type="button" aria-label="Delivery location">
          <MapPin size={17} />
          <span>
            <small>Delivering to</small>
            <strong>Choose your location</strong>
          </span>
          <ChevronDown size={14} />
        </button>

        <form
          className="search-bar"
          onSubmit={(event) => {
            event.preventDefault()
            document.getElementById('shop')?.scrollIntoView({ behavior: 'smooth' })
          }}
          role="search"
        >
          <label className="search-category" htmlFor="store-search">
            All <ChevronDown size={13} />
          </label>
          <input
            id="store-search"
            type="search"
            placeholder="Search something you’ll love..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" className="search-submit" aria-label="Search">
            <Search size={20} />
          </button>
        </form>

        <div className="header-actions">
          <button
            className="account-button"
            type="button"
            aria-label={authUser ? 'Sign out' : 'Sign in'}
            onClick={() => authUser ? signOut() : setAuthMode('login')}
          >
            <UserRound size={19} />
            <span>
              <small>Hello, {authUser?.first_name || 'guest'}</small>
              <strong>{authUser ? 'Sign out' : 'Sign in'}</strong>
            </span>
          </button>
          <button
            className="orders-button"
            type="button"
            onClick={() => !authUser && setAuthMode('login')}
          >
            <PackageCheck size={19} />
            <span><small>Your</small><strong>Orders</strong></span>
          </button>
          <button
            className="cart-button"
            type="button"
            onClick={() => setCartOpen(true)}
            aria-label={`Open cart, ${cartCount} items`}
          >
            <span className="cart-icon-wrap">
              <ShoppingCart size={23} />
              <span className="cart-count">{cartCount}</span>
            </span>
            <strong>Cart</strong>
          </button>
        </div>
      </header>

      <nav className={`category-nav ${mobileNavOpen ? 'is-open' : ''}`}>
        <button
          className="nav-all"
          type="button"
          onClick={() => setMobileNavOpen((open) => !open)}
        >
          <Menu size={18} /> All departments
        </button>
        <div className="nav-links">
          <button type="button" onClick={() => showCategory('All')}>Today&apos;s picks</button>
          <button type="button" onClick={() => showCategory('Electronics')}>Electronics</button>
          <button type="button" onClick={() => showCategory('Home')}>Home & living</button>
          <button type="button" onClick={() => showCategory('Fashion')}>Style</button>
          <button type="button" onClick={() => showCategory('Kitchen')}>Kitchen</button>
        </div>
        <span className="nav-promo"><span className="promo-dot" /> Fresh finds, every day</span>
      </nav>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="hero-eyebrow"><Sparkles size={14} /> THE LITTLE THINGS SALE</span>
            <h1>Good things.<br /><em>Great prices.</em></h1>
            <p>Everyday essentials and delightful discoveries, picked just for you.</p>
            <button className="hero-cta" type="button" onClick={() => showCategory('All')}>
              Shop the edit <ArrowRight size={17} />
            </button>
            <div className="hero-note">
              <span className="note-avatars"><i>J</i><i>M</i><i>A</i></span>
              <span>Loved by <strong>12,000+</strong> happy shoppers</span>
            </div>
          </div>
          <div className="hero-art" aria-label="A curated collection of everyday finds">
            <div className="hero-sticker"><span>GOOD<br />FINDS</span><Star size={15} fill="currentColor" /></div>
            <div className="hero-image hero-image-large">
              <img src={imageUrl('photo-1490481651871-ab68de25d43d', 900)} alt="A curated fashion collection" />
            </div>
            <div className="hero-image hero-image-small">
              <img src={imageUrl('photo-1505740420928-5e560c06d30e', 400)} alt="Studio headphones" />
            </div>
            <div className="hero-floating-card">
              <span className="floating-icon"><Check size={15} /></span>
              <span><strong>Picked with care</strong><small>Just for your everyday</small></span>
            </div>
            <span className="hero-sparkle sparkle-one">✳</span>
            <span className="hero-sparkle sparkle-two">✦</span>
          </div>
        </section>

        <section className="perks" aria-label="Shopping benefits">
          <div className="perk">
            <span className="perk-icon"><Truck size={18} /></span>
            <span><strong>Fast, free delivery</strong><small>On orders over ₹999</small></span>
          </div>
          <div className="perk">
            <span className="perk-icon"><ShieldCheck size={18} /></span>
            <span><strong>Shop with confidence</strong><small>Easy 30-day returns</small></span>
          </div>
          <div className="perk">
            <span className="perk-icon"><Heart size={18} /></span>
            <span><strong>Good things, guaranteed</strong><small>Quality you can count on</small></span>
          </div>
          <div className="perk">
            <span className="perk-icon"><PackageCheck size={18} /></span>
            <span><strong>Thoughtful picks</strong><small>Curated for real life</small></span>
          </div>
        </section>

        <section className="category-section">
          <div className="section-heading">
            <div>
              <span className="section-kicker">A LITTLE SOMETHING FOR EVERYONE</span>
              <h2>Explore by category</h2>
            </div>
            <button className="text-link" type="button" onClick={() => showCategory('All')}>
              Browse everything <ArrowRight size={15} />
            </button>
          </div>
          <div className="category-cards">
            <button className="category-card category-electronics" onClick={() => showCategory('Electronics')} type="button">
              <img src={imageUrl('photo-1498049794561-7780e7231661', 600)} alt="" />
              <span><strong>Tech & gadgets</strong><small>Everyday upgrades</small></span>
              <ChevronRight size={18} />
            </button>
            <button className="category-card category-home" onClick={() => showCategory('Home')} type="button">
              <img src={imageUrl('photo-1600210492486-724fe5c67fb0', 600)} alt="" />
              <span><strong>Home & living</strong><small>Make room for cozy</small></span>
              <ChevronRight size={18} />
            </button>
            <button className="category-card category-style" onClick={() => showCategory('Fashion')} type="button">
              <img src={imageUrl('photo-1483985988355-763728e1935b', 600)} alt="" />
              <span><strong>Style & accessories</strong><small>Wear it your way</small></span>
              <ChevronRight size={18} />
            </button>
            <button className="category-card category-kitchen" onClick={() => showCategory('Kitchen')} type="button">
              <img src={imageUrl('photo-1556911220-e15b29be8c8f', 600)} alt="" />
              <span><strong>Kitchen favorites</strong><small>Made for good meals</small></span>
              <ChevronRight size={18} />
            </button>
          </div>
        </section>

        <section className="shop-section" id="shop">
          <div className="shop-heading">
            <div>
              <span className="section-kicker">THE GOOD STUFF</span>
              <h2>{query ? `Results for “${query}”` : 'Popular right now'}</h2>
              <p>{visibleProducts.length} thoughtful finds, ready to make your day.</p>
            </div>
            <label className="sort-control">
              <SlidersHorizontal size={16} />
              <span>Sort by</span>
              <select value={sort} onChange={(event) => setSort(event.target.value)} aria-label="Sort products">
                <option value="featured">Featured</option>
                <option value="price-low">Price: low to high</option>
                <option value="price-high">Price: high to low</option>
                <option value="rating">Top rated</option>
              </select>
              <ChevronDown size={14} />
            </label>
          </div>

          <div className="shop-layout">
            <aside className="filter-sidebar">
              <h3>Departments</h3>
              <div className="filter-list">
                {categories.map((item) => (
                  <button
                    className={category === item ? 'filter-active' : ''}
                    key={item}
                    type="button"
                    onClick={() => setCategory(item)}
                  >
                    <span>{item === 'All' ? 'Everything' : item}</span>
                    {category === item && <ChevronRight size={15} />}
                  </button>
                ))}
              </div>
              <div className="sidebar-note">
                <Sparkles size={17} />
                <strong>A little more joy.</strong>
                <span>Discover thoughtful finds for less, every single day.</span>
              </div>
            </aside>

            <div className="product-area">
              <div className="product-toolbar">
                <div className="category-pills">
                  {categories.map((item) => (
                    <button
                      className={category === item ? 'pill-active' : ''}
                      key={item}
                      type="button"
                      onClick={() => setCategory(item)}
                    >
                      {item === 'All' ? 'All finds' : item}
                    </button>
                  ))}
                </div>
                <span className="results-count">{visibleProducts.length} items</span>
              </div>

              {productsLoading ? (
                <div className="catalog-status" role="status">Finding the good stuff…</div>
              ) : productError ? (
                <div className="catalog-status catalog-error" role="alert">{productError}</div>
              ) : visibleProducts.length ? (
                <div className="product-grid">
                  {visibleProducts.map((product) => (
                    <article className="product-card" key={product.id}>
                      <div className={`product-image ${product.color}`}>
                        <img src={product.image} alt={product.name} loading="lazy" />
                        <span className="product-badge">{product.badge}</span>
                        <button
                          className={`favorite-button ${favorites.includes(product.id) ? 'is-favorite' : ''}`}
                          type="button"
                          aria-label={favorites.includes(product.id) ? 'Remove from favorites' : 'Add to favorites'}
                          onClick={() => toggleFavorite(product.id)}
                        >
                          <Heart size={17} fill={favorites.includes(product.id) ? 'currentColor' : 'none'} />
                        </button>
                        {cart[product.id] > 0 && <span className="in-cart-badge">{cart[product.id]} in cart</span>}
                      </div>
                      <div className="product-info">
                        <span className="product-category">{product.category}</span>
                        <h3>{product.name}</h3>
                        <p className="product-detail">{product.detail}</p>
                        {product.imageAttribution && product.imageSourceUrl && (
                          <div className="product-image-credit">
                            Photo: <a href={product.imageSourceUrl} target="_blank" rel="noreferrer">
                              {product.imageAttribution}
                            </a>
                            {product.imageLicense && (
                              <>
                                {' · '}
                                <a
                                  href={product.imageLicenseUrl || product.imageSourceUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  {product.imageLicense}
                                </a>
                              </>
                            )}
                          </div>
                        )}
                        <div className="product-rating">
                          <span className="rating-stars"><Star size={13} fill="currentColor" /> {product.rating}</span>
                          <span>({product.reviews.toLocaleString('en-IN')})</span>
                        </div>
                        <div className="product-bottom">
                          <div className="price-block">
                            <strong>{money(product.price)}</strong>
                            <del>{money(product.oldPrice)}</del>
                          </div>
                          <button
                            className={`add-button ${cart[product.id] ? 'added' : ''}`}
                            type="button"
                            onClick={() => addToCart(product.id)}
                            aria-label={`Add ${product.name} to cart`}
                          >
                            {cart[product.id] ? <Check size={16} /> : <Plus size={17} />}
                            <span>{cart[product.id] ? 'Add one' : 'Add'}</span>
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-results">
                  <span><Search size={25} /></span>
                  <h3>No finds just yet</h3>
                  <p>Try a different search or browse all of our good stuff.</p>
                  <button type="button" onClick={() => { setQuery(''); setCategory('All') }}>Show me everything</button>
                </div>
              )}
            </div>
          </div>
        </section>

      </main>

      <section className="footer-trust-strip" aria-label="Shopping highlights">
        <div className="footer-inner footer-trust-grid">
          <div className="footer-trust-item">
            <span className="footer-trust-icon"><Truck size={20} /></span>
            <span><strong>Free &amp; fast delivery</strong><small>On orders above ₹999</small></span>
          </div>
          <div className="footer-trust-item">
            <span className="footer-trust-icon"><LockKeyhole size={20} /></span>
            <span><strong>Secure account access</strong><small>Sign in to manage your profile</small></span>
          </div>
          <div className="footer-trust-item">
            <span className="footer-trust-icon"><BadgeCheck size={20} /></span>
            <span><strong>Thoughtful everyday finds</strong><small>Explore all four departments</small></span>
          </div>
          <div className="footer-trust-item">
            <span className="footer-trust-icon"><Headset size={20} /></span>
            <span><strong>Here to help</strong><small>Customer account and catalog access</small></span>
          </div>
        </div>
      </section>

      <section className="newsletter footer-newsletter" aria-labelledby="footer-newsletter-title">
        <div className="footer-inner footer-newsletter-inner">
          <div className="footer-newsletter-copy">
            <span className="footer-eyebrow">EXCLUSIVE SAVINGS</span>
            <h2 id="footer-newsletter-title">Good finds, straight to your inbox.</h2>
            <p>Sign up for updates on new arrivals and offers from Pexo Market.</p>
          </div>
          <form className="newsletter-form" onSubmit={(event) => event.preventDefault()}>
            <Mail size={18} aria-hidden="true" />
            <label className="sr-only" htmlFor="newsletter-email">Email address</label>
            <input id="newsletter-email" type="email" placeholder="Enter your email address" />
            <button type="submit">Subscribe <ArrowRight size={16} /></button>
          </form>
        </div>
      </section>

      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-main">
            <section className="footer-about">
              <a className="brand footer-brand" href="#" aria-label="Pexo Market home">
                <img className="brand-logo" src={logoImage} alt="Pexo Market" />
              </a>
              <p>Everyday essentials, thoughtful finds, and little things that make life feel good.</p>
              <div className="footer-account-card">
                <span className="footer-account-icon"><UserRound size={19} /></span>
                <span><small>Your Pexo account</small><strong>Good to have you here</strong></span>
                <button type="button" onClick={() => setAuthMode('login')}>Sign in</button>
              </div>
            </section>

            <section className="footer-column">
              <h2>About Pexo</h2>
              <p>Discover everyday picks across our curated departments.</p>
              <button type="button" onClick={() => showCategory('All')}>Explore the shop</button>
              <button type="button" onClick={() => showCategory('All')}>New and popular finds</button>
              <button type="button" onClick={() => setAuthMode('register')}>Join the Pexo community</button>
            </section>

            <section className="footer-column">
              <h2>Customer care</h2>
              <button type="button" onClick={() => setAuthMode('login')}>Your account</button>
              <button type="button" onClick={() => showCategory('All')}>Browse the catalog</button>
              <button type="button" onClick={() => document.getElementById('newsletter-email')?.focus()}>
                Get shop updates
              </button>
              <span className="footer-help-note"><RefreshCw size={14} /> Free delivery on orders above ₹999</span>
            </section>

            <section className="footer-column">
              <h2>Top departments</h2>
              {categories.filter((item) => item !== 'All').map((item) => (
                <button key={item} type="button" onClick={() => showCategory(item)}>
                  {item === 'Home' ? 'Home & Living' : item}
                </button>
              ))}
            </section>

            <section className="footer-column footer-app-column">
              <h2>Shop with Pexo</h2>
              <p>Take your time, find your favorites, and make yourself at home.</p>
              <div className="footer-app-badges" aria-label="Mobile apps coming soon">
                <div className="footer-app-badge"><Smartphone size={21} /><span><small>COMING SOON</small><strong>Android app</strong></span></div>
                <div className="footer-app-badge"><Smartphone size={21} /><span><small>COMING SOON</small><strong>iOS app</strong></span></div>
              </div>
              <h3>Follow along</h3>
              <div className="footer-socials" aria-label="Social links coming soon">
                <span title="Instagram coming soon"><Camera size={17} /></span>
                <span title="YouTube coming soon"><CirclePlay size={17} /></span>
                <span title="Facebook coming soon"><UsersRound size={17} /></span>
              </div>
            </section>
          </div>

          <div className="footer-security-row">
            <div className="footer-security-label"><ShieldCheck size={16} /> SECURE CUSTOMER ACCOUNT</div>
            <div className="footer-security-note"><LockKeyhole size={14} /> Sign-in protected with JWT authentication</div>
            <div className="footer-security-note"><PackageCheck size={14} /> Browse Electronics, Fashion, Home &amp; Kitchen</div>
          </div>

          <div className="footer-bottom">
            <span>© 2026 Pexo Market. All rights reserved.</span>
            <span>Everyday finds for a life well lived.</span>
          </div>
        </div>
      </footer>

      {cartOpen && (
        <div className="cart-overlay" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setCartOpen(false)
        }}>
          <aside className="cart-drawer" role="dialog" aria-modal="true" aria-labelledby="cart-title">
            <div className="drawer-heading">
              <div><span className="section-kicker">YOUR GOOD FINDS</span><h2 id="cart-title">Your cart <span>({cartCount})</span></h2></div>
              <button type="button" className="drawer-close" onClick={() => setCartOpen(false)} aria-label="Close cart"><X size={20} /></button>
            </div>
            {cartItems.length ? (
              <>
                <div className="cart-items">
                  {cartItems.map((product) => (
                    <div className="cart-item" key={product.id}>
                      <img src={product.image} alt="" />
                      <div className="cart-item-details">
                        <span className="product-category">{product.category}</span>
                        <strong>{product.name}</strong>
                        <span className="cart-item-price">{money(product.price)}</span>
                        {product.imageAttribution && product.imageSourceUrl && (
                          <span className="cart-image-credit">
                            Photo: <a href={product.imageSourceUrl} target="_blank" rel="noreferrer">
                              {product.imageAttribution}
                            </a>
                            {product.imageLicense && (
                              <>
                                {' · '}
                                <a
                                  href={product.imageLicenseUrl || product.imageSourceUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  {product.imageLicense}
                                </a>
                              </>
                            )}
                          </span>
                        )}
                        <div className="quantity-control">
                          <button type="button" aria-label={`Remove one ${product.name}`} onClick={() => changeQuantity(product.id, -1)}><Minus size={13} /></button>
                          <span>{cart[product.id]}</span>
                          <button type="button" aria-label={`Add one ${product.name}`} onClick={() => changeQuantity(product.id, 1)}><Plus size={13} /></button>
                        </div>
                      </div>
                      <button className="remove-item" type="button" aria-label={`Remove ${product.name} from cart`} onClick={() => changeQuantity(product.id, -cart[product.id])}><X size={16} /></button>
                    </div>
                  ))}
                </div>
                <div className="cart-summary">
                  <div className="shipping-message"><Truck size={16} /><span>{subtotal >= 999 ? 'You’ve unlocked free delivery!' : `Add ${money(999 - subtotal)} more for free delivery`}</span></div>
                  <div className="subtotal-row"><span>Subtotal</span><strong>{money(subtotal)}</strong></div>
                  <p>Taxes and delivery are calculated at checkout.</p>
                  <button className="checkout-button" type="button">Continue to checkout <ArrowRight size={17} /></button>
                  <button className="continue-shopping" type="button" onClick={() => setCartOpen(false)}>Keep finding good stuff</button>
                </div>
              </>
            ) : (
              <div className="empty-cart">
                <span><ShoppingCart size={27} /></span>
                <h3>Your cart is taking a little break.</h3>
                <p>Find something lovely to bring it back to life.</p>
                <button type="button" onClick={() => setCartOpen(false)}>Start exploring <ArrowRight size={16} /></button>
              </div>
            )}
          </aside>
        </div>
      )}
      {authMode && (
        <AuthPage
          initialMode={authMode}
          onAuthenticated={(user) => {
            setAuthUser(user)
            setAuthMode(null)
          }}
          onClose={() => setAuthMode(null)}
        />
      )}
    </div>
  )
}

export default App
