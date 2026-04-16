from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
import uuid
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'votingbox-secret-key-2026-group2')

# ─── In-Memory Data Stores ───────────────────────────────────────────────────

USERS = {}  # email -> {uid, email, name, role, password, voted_elections, vote_history}

ELECTIONS = [
    {
        'id': '1',
        'title': 'National Student Council Election 2026',
        'category': 'Student Council',
        'icon': 'graduation-cap',
        'deadline': 'March 20, 2026',
        'deadline_raw': '2026-03-20',
        'status': 'CLOSED',
        'created_by': 'admin',
    },
    {
        'id': '2',
        'title': 'Municipal Board of Directors',
        'category': 'Municipal',
        'icon': 'building-2',
        'deadline': 'April 30, 2026',
        'deadline_raw': '2026-04-30',
        'status': 'OPEN',
        'created_by': 'admin',
    },
    {
        'id': '3',
        'title': 'Corporate Employee Representative',
        'category': 'Corporate',
        'icon': 'briefcase',
        'deadline': 'May 10, 2026',
        'deadline_raw': '2026-05-10',
        'status': 'OPEN',
        'created_by': 'admin',
    },
]

# All candidate lists — keyed by election_id
CANDIDATES = {
    '1': [
        {'id': 'c1', 'name': 'Narendra Modi',    'party': 'National Democratic Alliance', 'desc': 'Incumbent leader focusing on national development and security.', 'color': '#FF9933', 'avatar_bg': 'FF9933', 'votes': 5420},
        {'id': 'c2', 'name': 'Rahul Gandhi',      'party': 'Indian National Congress',    'desc': 'Advocating for social justice and economic equality.',             'color': '#138808', 'avatar_bg': '138808', 'votes': 3890},
        {'id': 'c3', 'name': 'Arvind Kejriwal',   'party': 'Aam Aadmi Party',             'desc': 'Focusing on education, healthcare, and anti-corruption.',           'color': '#00B2EF', 'avatar_bg': '00B2EF', 'votes': 2150},
        {'id': 'c4', 'name': 'Mamata Banerjee',   'party': 'All India Trinamool Congress','desc': 'Championing regional development and grassroots empowerment.',       'color': '#00CCFF', 'avatar_bg': '00CCFF', 'votes': 1990},
    ],
    '2': [
        {'id': 'c5', 'name': 'Local Candidate A', 'party': 'City Forward',    'desc': 'Focusing on urban development and infrastructure.', 'color': '#649748', 'avatar_bg': '649748', 'votes': 0},
        {'id': 'c6', 'name': 'Local Candidate B', 'party': 'Community First', 'desc': 'Advocating for better schools and healthcare.',       'color': '#A8D672', 'avatar_bg': 'A8D672', 'votes': 0},
    ],
    '3': [
        {'id': 'c7', 'name': 'Priya Sharma', 'party': 'Employee Alliance', 'desc': 'Fighting for better work conditions and employee benefits.',           'color': '#FF6B6B', 'avatar_bg': 'FF6B6B', 'votes': 0},
        {'id': 'c8', 'name': 'Rahul Verma',  'party': 'Workers United',    'desc': 'Advocating for fair wages and transparent management.', 'color': '#4ECDC4', 'avatar_bg': '4ECDC4', 'votes': 0},
    ],
}

# Audit log — list of dicts
AUDIT_LOG = [
    {'time': '2026-03-22 10:05:23', 'user': 'voter_101',  'action': 'Vote Cast',      'ip': '103.21.45.12', 'status': 'Success'},
    {'time': '2026-03-22 10:12:11', 'user': 'admin_001',  'action': 'Login',          'ip': '192.168.1.10', 'status': 'Success'},
    {'time': '2026-03-22 10:18:44', 'user': 'voter_210',  'action': 'Vote Attempt',   'ip': '192.168.1.45', 'status': 'Blocked'},
    {'time': '2026-03-22 10:25:01', 'user': 'voter_302',  'action': 'Register',       'ip': '45.67.89.01',  'status': 'Success'},
    {'time': '2026-03-22 11:00:00', 'user': 'voter_8821', 'action': 'Login via VPN',  'ip': '10.0.0.1',     'status': 'Warning'},
]

FORUM_POSTS = [
    {'id': 'p1', 'author': 'Priya Sharma', 'verified': True,  'time': '2 hours ago', 'text': 'The new infrastructure proposal is exactly what our district needs. It will reduce traffic by 30% and create thousands of jobs.', 'upvotes': 145, 'downvotes': 12,  'replies': 24},
    {'id': 'p2', 'author': 'Rahul Verma',  'verified': False, 'time': '4 hours ago', 'text': "I'm concerned about the budget allocation for the education sector. We need more transparency in how these funds are distributed.", 'upvotes': 89,  'downvotes': 45,  'replies': 12},
    {'id': 'p3', 'author': 'Amit Patel',   'verified': True,  'time': '6 hours ago', 'text': 'Digital voting is the future. Glad to see VotingBox implementing such secure measures. The blockchain integration is impressive.',   'upvotes': 320, 'downvotes': 5,   'replies': 56},
]

DEBATE_POSTS = [
    {'id': 'd1', 'author': 'Rahul S.', 'candidate': 'Narendra Modi',  'candidate_color': '#FF9933', 'time': '1 hour ago',  'text': 'The infrastructure development in the last 5 years has been unprecedented. We need continuity for the next phase.', 'tags': ['Economy', 'Infrastructure'], 'upvotes': 342, 'downvotes': 12},
    {'id': 'd2', 'author': 'Priya M.', 'candidate': 'Rahul Gandhi',   'candidate_color': '#138808', 'time': '2 hours ago', 'text': "We need a stronger focus on employment and youth opportunities. The current policies aren't addressing the middle class.", 'tags': ['Jobs', 'Youth'],           'upvotes': 289, 'downvotes': 45},
    {'id': 'd3', 'author': 'Amit K.',  'candidate': 'Arvind Kejriwal','candidate_color': '#00B2EF', 'time': '3 hours ago', 'text': 'The Delhi model of education and healthcare needs to be replicated nationwide. Basic amenities should be a right.',       'tags': ['Education', 'Healthcare'],  'upvotes': 412, 'downvotes': 88},
]

ARCHIVE_DATA = [
    {'name': 'National General Election 2024', 'category': 'National',   'date': 'May 15, 2024',  'total_votes': '642M', 'winner': 'Narendra Modi',    'results': [{'name': 'Narendra Modi',    'pct': 45}, {'name': 'Rahul Gandhi',    'pct': 32}, {'name': 'Others', 'pct': 23}]},
    {'name': 'State Assembly Election 2023',   'category': 'State',      'date': 'Nov 10, 2023',  'total_votes': '45M',  'winner': 'Mamata Banerjee',  'results': [{'name': 'Mamata Banerjee',  'pct': 48}, {'name': 'BJP',             'pct': 38}, {'name': 'Others', 'pct': 14}]},
    {'name': 'Municipal Corporation 2022',     'category': 'Local',      'date': 'Dec 05, 2022',  'total_votes': '12M',  'winner': 'Arvind Kejriwal',  'results': [{'name': 'Arvind Kejriwal',  'pct': 53}, {'name': 'BJP',             'pct': 35}, {'name': 'Others', 'pct': 12}]},
    {'name': 'University Senate 2025',         'category': 'Education',  'date': 'Jan 20, 2025',  'total_votes': '45K',  'winner': 'Priya Sharma',     'results': [{'name': 'Priya Sharma',     'pct': 62}, {'name': 'Rohit Kumar',     'pct': 28}, {'name': 'Others', 'pct': 10}]},
]

DEMO_ACCOUNTS = {
    'voter@example.com':    {'password': 'voter123',    'name': 'Demo Voter',       'role': 'voter'},
    'admin@example.com':    {'password': 'admin123',    'name': 'Admin User',       'role': 'admin'},
    'observer@example.com': {'password': 'observer123', 'name': 'Election Observer','role': 'observer'},
}

# Candidate colour palette for admin-created elections
CANDIDATE_COLORS = ['#FF9933','#138808','#00B2EF','#A8D672','#FF6B6B','#4ECDC4','#F7B731','#8B5CF6','#EF4444','#10B981']

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_current_user():
    return session.get('user')

def log_action(user_label, action, status='Success'):
    AUDIT_LOG.insert(0, {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user': user_label,
        'action': action,
        'ip': request.remote_addr or '127.0.0.1',
        'status': status,
    })

def build_results_data():
    """Build live results from CANDIDATES vote counts."""
    rd = {}
    for eid, clist in CANDIDATES.items():
        election = next((e for e in ELECTIONS if e['id'] == eid), None)
        if not election:
            continue
        total = sum(c.get('votes', 0) for c in clist)
        rd[eid] = {
            'title': election['title'],
            'status': 'LIVE' if election['status'] == 'OPEN' else election['status'],
            'candidates': [
                {
                    'name': c['name'],
                    'party': c['party'],
                    'votes': c.get('votes', 0),
                    'color': c['color'],
                    'avatar_bg': c['avatar_bg'],
                }
                for c in clist
            ],
            'total': max(total, 1),
        }
    return rd

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    user = get_current_user()
    open_elections = [e for e in ELECTIONS if e['status'] == 'OPEN']
    return render_template('index.html', user=user, open_elections=open_elections[:3])

@app.route('/elections')
def elections():
    user = get_current_user()
    return render_template('elections.html', user=user, elections=ELECTIONS)

@app.route('/vote/<election_id>', methods=['GET'])
def vote(election_id):
    if not session.get('user'):
        return redirect(url_for('auth') + '?redirect=/vote/' + election_id)
    user = get_current_user()
    election = next((e for e in ELECTIONS if e['id'] == election_id), None)
    if not election:
        return redirect(url_for('elections'))
    candidates = CANDIDATES.get(election_id, [])
    voted_elections = user.get('voted_elections', []) if user else []
    already_voted = election_id in voted_elections
    return render_template('vote.html', user=user, election=election,
                           candidates=candidates, already_voted=already_voted)

@app.route('/vote/<election_id>', methods=['POST'])
def submit_vote(election_id):
    if not session.get('user'):
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json() or request.form
    candidate_id   = data.get('candidate_id')
    candidate_name = data.get('candidate_name', '')
    user = session['user']

    if 'voted_elections' not in user:
        user['voted_elections'] = []
    if election_id in user['voted_elections']:
        return jsonify({'success': False, 'error': 'Already voted'}), 400

    user['voted_elections'].append(election_id)
    if 'vote_history' not in user:
        user['vote_history'] = []
    receipt = 'TXN-' + uuid.uuid4().hex[:8].upper()
    user['vote_history'].append({
        'election_id': election_id,
        'candidate':   candidate_name,
        'receipt':     receipt,
        'date':        datetime.now().strftime('%B %d, %Y'),
    })
    session['user'] = user
    session.modified = True

    # Increment vote count on the candidate
    for c in CANDIDATES.get(election_id, []):
        if c['id'] == candidate_id:
            c['votes'] = c.get('votes', 0) + 1
            break

    # Persist updated votes to USERS store if registered
    email = user.get('email', '')
    if email in USERS:
        USERS[email]['voted_elections'] = user['voted_elections']
        USERS[email]['vote_history']    = user['vote_history']

    log_action(user.get('name', 'voter'), f'Vote Cast → {candidate_name} (Election {election_id})')
    return jsonify({'success': True, 'candidate': candidate_name, 'receipt': receipt})

@app.route('/results')
def results():
    user = get_current_user()
    return render_template('results.html', user=user, results_data=build_results_data())

@app.route('/api/results/<election_id>')
def api_results(election_id):
    """JSON endpoint for live result polling."""
    rd = build_results_data()
    if election_id not in rd:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(rd[election_id])

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('auth'))
    user = get_current_user()
    voted_elections = user.get('voted_elections', [])
    vote_history    = user.get('vote_history', [])
    elections_with_status = []
    for e in ELECTIONS:
        e_copy = dict(e)
        e_copy['voted'] = e['id'] in voted_elections
        elections_with_status.append(e_copy)
    voter_id = user.get('uid', '')[:12].upper()
    return render_template('dashboard.html', user=user, elections=elections_with_status,
                           vote_history=vote_history, voter_id=voter_id,
                           votes_cast=len(voted_elections))

@app.route('/auth')
def auth():
    user = get_current_user()
    if user:
        return redirect(url_for('dashboard'))
    redirect_to = request.args.get('redirect', '/dashboard')
    return render_template('auth.html', user=None, redirect_to=redirect_to)

@app.route('/auth/login', methods=['POST'])
def login():
    data        = request.get_json() or request.form
    email       = data.get('email', '').strip().lower()
    password    = data.get('password', '')
    redirect_to = data.get('redirect', '/dashboard')

    # Demo accounts
    if email in DEMO_ACCOUNTS and DEMO_ACCOUNTS[email]['password'] == password:
        acc = DEMO_ACCOUNTS[email]
        uid = str(uuid.uuid4())
        session['user'] = {
            'uid': uid, 'email': email, 'name': acc['name'],
            'role': acc['role'], 'voted_elections': [], 'vote_history': [],
        }
        session.modified = True
        log_action(acc['name'], 'Login')
        # Admin goes to admin panel
        if acc['role'] == 'admin' and redirect_to == '/dashboard':
            redirect_to = '/admin'
        return jsonify({'success': True, 'redirect': redirect_to})

    # Registered users
    if email in USERS and USERS[email]['password'] == password:
        u = USERS[email]
        session['user'] = {
            'uid': u['uid'], 'email': email, 'name': u['name'],
            'role': u.get('role', 'voter'),
            'voted_elections': u.get('voted_elections', []),
            'vote_history':    u.get('vote_history', []),
        }
        session.modified = True
        log_action(u['name'], 'Login')
        return jsonify({'success': True, 'redirect': redirect_to})

    log_action(email, 'Failed Login', 'Blocked')
    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

@app.route('/auth/register', methods=['POST'])
def register():
    data     = request.get_json() or request.form
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    if email in USERS or email in DEMO_ACCOUNTS:
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    uid = str(uuid.uuid4())
    USERS[email] = {
        'uid': uid, 'email': email, 'name': name, 'password': password,
        'role': 'voter', 'voted_elections': [], 'vote_history': [],
        'registered': datetime.now().strftime('%Y-%m-%d'),
    }
    session['user'] = {
        'uid': uid, 'email': email, 'name': name,
        'role': 'voter', 'voted_elections': [], 'vote_history': [],
    }
    session.modified = True
    log_action(name, 'Register')
    return jsonify({'success': True, 'redirect': '/dashboard'})

@app.route('/auth/logout')
def logout():
    user = get_current_user()
    if user:
        log_action(user.get('name', 'user'), 'Logout')
    session.clear()
    return redirect(url_for('index'))

# ─── Ask AI ──────────────────────────────────────────────────────────────────

@app.route('/ask-ai')
def ask_ai():
    user = get_current_user()
    return render_template('ask_ai.html', user=user)

@app.route('/api/ask-ai', methods=['POST'])
def api_ask_ai():
    question = (request.get_json() or {}).get('question', '').strip()
    if not question:
        return jsonify({'success': False, 'error': 'Empty question'}), 400

    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            system_prompt = (
                "You are an expert on Indian elections, voting history, democracy, and political science. "
                "Answer questions clearly, in detail, and educationally. "
                "Use markdown formatting (headers, bullet points, bold) to structure your response."
            )
            response = model.generate_content(f"{system_prompt}\n\nUser question: {question}")
            return jsonify({'success': True, 'answer': response.text})
        except Exception as e:
            print(f"[Gemini Error] {e}")
            # Fall through to mock

    # ── Fallback mock responses ──
    q = question.lower()
    mock_map = {
        'election commission': (
            "## Election Commission of India\n\n"
            "The **ECI** was established on **January 25, 1950**. It is an autonomous constitutional authority.\n\n"
            "### Key Facts\n- **First CEC:** Sukumar Sen\n- **HQ:** Nirvachan Sadan, New Delhi\n"
            "- Enforces the **Model Code of Conduct** during elections.\n\n"
            "The ECI conducts free and fair elections for Parliament, State Assemblies, President and Vice-President of India."
        ),
        'evm': (
            "## Electronic Voting Machines (EVMs)\n\n"
            "EVMs were introduced experimentally in **Kerala in 1982** and adopted nationwide in **2004**.\n\n"
            "### Components\n1. **Ballot Unit** — Voter presses candidate button\n"
            "2. **Control Unit** — Operated by polling officer\n"
            "3. **VVPAT** — Voter Verifiable Paper Audit Trail (since 2013)\n\n"
            "EVMs have **no internet connectivity** and use one-time programmable chips."
        ),
        'nota': (
            "## NOTA — None of the Above\n\n"
            "NOTA was introduced in India by the Supreme Court in **2013**. It allows voters to reject all "
            "candidates on the ballot.\n\n"
            "- First used in **5 state assembly elections** in Nov–Dec 2013\n"
            "- Represented by a **ballot box with a cross** symbol\n"
            "- NOTA votes are counted but **do not affect the result** — the candidate with most votes still wins."
        ),
        'first election': (
            "## India's First General Election (1951–52)\n\n"
            "India's first general election was held from **October 25, 1951 to February 21, 1952** — a process "
            "spanning 4 months.\n\n"
            "### Key Facts\n- **176 million** eligible voters\n- **489 Lok Sabha seats**\n"
            "- **Indian National Congress** won with 364 seats\n"
            "- **Jawaharlal Nehru** became the first elected Prime Minister\n"
            "- Literacy was only ~16%, so **symbols were used** instead of names."
        ),
    }
    for key, resp in mock_map.items():
        if key in q:
            return jsonify({'success': True, 'answer': resp})

    return jsonify({'success': True, 'answer': (
        f"## VotingBox AI — Response\n\nYou asked: **\"{question}\"**\n\n"
        "I'm specialised in Indian elections and democratic processes. Here's what I can help with:\n\n"
        "- 🗳️ **Election History** — From 1951 to present\n"
        "- 🏛️ **Election Commission** — Role, powers, structure\n"
        "- 🖥️ **EVMs & VVPAT** — How electronic voting works\n"
        "- ⚖️ **Electoral Reforms** — RTI, NOTA, voter ID\n"
        "- 📊 **Voting Systems** — FPTP, PR, ranked-choice\n"
        "- 📜 **Constitutional Provisions** — Articles 324–329\n\n"
        "*To enable full AI responses, set your `GEMINI_API_KEY` in the `.env` file.*"
    )})

# ─── Blockchain ───────────────────────────────────────────────────────────────

@app.route('/blockchain')
def blockchain():
    user = get_current_user()
    return render_template('blockchain.html', user=user)

# ─── Leaderboard ─────────────────────────────────────────────────────────────

@app.route('/leaderboard')
def leaderboard():
    user = get_current_user()
    return render_template('leaderboard.html', user=user)

# ─── Forum ────────────────────────────────────────────────────────────────────

@app.route('/forum')
def forum():
    user = get_current_user()
    return render_template('forum.html', user=user, posts=FORUM_POSTS)

@app.route('/forum/post', methods=['POST'])
def forum_post():
    data = request.get_json() or {}
    u = get_current_user()
    new_post = {
        'id':        'p' + str(len(FORUM_POSTS) + 1),
        'author':    u['name'] if u else data.get('author', 'Anonymous'),
        'verified':  u and u.get('role') in ('admin', 'observer'),
        'time':      'Just now',
        'text':      data.get('text', '').strip(),
        'upvotes':   0,
        'downvotes': 0,
        'replies':   0,
    }
    if not new_post['text']:
        return jsonify({'success': False, 'error': 'Empty post'}), 400
    FORUM_POSTS.insert(0, new_post)
    return jsonify({'success': True, 'post': new_post})

# ─── Debate ───────────────────────────────────────────────────────────────────

@app.route('/debate')
def debate():
    user = get_current_user()
    return render_template('debate.html', user=user, posts=DEBATE_POSTS)

@app.route('/debate/vote', methods=['POST'])
def debate_vote():
    data      = request.get_json() or {}
    post_id   = data.get('post_id')
    vote_type = data.get('type')
    for post in DEBATE_POSTS:
        if post['id'] == post_id:
            if vote_type == 'up':
                post['upvotes']   += 1
            else:
                post['downvotes'] += 1
            return jsonify({'success': True, 'upvotes': post['upvotes'], 'downvotes': post['downvotes']})
    return jsonify({'success': False}), 404

# ─── Static Pages ─────────────────────────────────────────────────────────────

@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html', user=get_current_user())

@app.route('/about')
def about():
    return render_template('about.html', user=get_current_user())

@app.route('/about-site')
def about_site():
    return render_template('about_site.html', user=get_current_user())

@app.route('/archive')
def archive():
    return render_template('archive.html', user=get_current_user(), archive=ARCHIVE_DATA)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = request.method == 'POST'
    return render_template('contact.html', user=get_current_user(), success=success)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', user=get_current_user())

@app.route('/terms')
def terms():
    return render_template('terms.html', user=get_current_user())

# ─── Admin Panel ──────────────────────────────────────────────────────────────

@app.route('/admin')
def admin():
    user     = get_current_user()
    is_admin = user and user.get('role') == 'admin'
    # Build real voter list from USERS + demo voter
    voters = [
        {
            'id':     v['uid'][:8].upper(),
            'name':   v['name'],
            'email':  v['email'],
            'date':   v.get('registered', '2026-01-01'),
            'status': 'Verified',
            'votes':  len(v.get('voted_elections', [])),
        }
        for v in USERS.values()
    ]
    return render_template('admin.html',
                           user=user,
                           is_admin=is_admin,
                           elections=ELECTIONS,
                           candidates=CANDIDATES,
                           voters=voters,
                           logs=AUDIT_LOG[:50])

# Admin: Create a new election (POST)
@app.route('/admin/create-election', methods=['POST'])
def admin_create_election():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data     = request.get_json() or {}
    title    = data.get('title', '').strip()
    category = data.get('category', 'General')
    deadline = data.get('deadline', '')
    status   = data.get('status', 'OPEN')

    if not title or not deadline:
        return jsonify({'success': False, 'error': 'Title and deadline required'}), 400

    eid = str(uuid.uuid4())[:8]
    ELECTIONS.append({
        'id':           eid,
        'title':        title,
        'category':     category,
        'icon':         'clipboard-list',
        'deadline':     datetime.strptime(deadline, '%Y-%m-%d').strftime('%B %d, %Y') if '-' in deadline else deadline,
        'deadline_raw': deadline,
        'status':       status,
        'created_by':   user['name'],
    })
    CANDIDATES[eid] = []  # empty candidate list to be filled next

    log_action(user['name'], f'Created Election: {title}')
    return jsonify({'success': True, 'election_id': eid, 'title': title})

# Admin: Add candidate to an election
@app.route('/admin/add-candidate', methods=['POST'])
def admin_add_candidate():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data        = request.get_json() or {}
    election_id = data.get('election_id', '')
    name        = data.get('name', '').strip()
    party       = data.get('party', '').strip() or 'Independent'
    desc        = data.get('desc', '').strip() or f'{name} is running as a candidate in this election.'

    if not election_id or not name:
        return jsonify({'success': False, 'error': 'election_id and name required'}), 400

    # Election must exist
    election = next((e for e in ELECTIONS if e['id'] == election_id), None)
    if not election:
        return jsonify({'success': False, 'error': 'Election not found'}), 404

    if election_id not in CANDIDATES:
        CANDIDATES[election_id] = []

    idx   = len(CANDIDATES[election_id])
    color = CANDIDATE_COLORS[idx % len(CANDIDATE_COLORS)]
    cid   = 'c-' + uuid.uuid4().hex[:6]
    candidate = {
        'id':        cid,
        'name':      name,
        'party':     party,
        'desc':      desc,
        'color':     color,
        'avatar_bg': color.lstrip('#'),
        'votes':     0,
    }
    CANDIDATES[election_id].append(candidate)
    log_action(user['name'], f'Added Candidate: {name} → Election {election_id}')
    return jsonify({'success': True, 'candidate': candidate})

# Admin: Toggle election status
@app.route('/admin/toggle-election', methods=['POST'])
def admin_toggle_election():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data        = request.get_json() or {}
    election_id = data.get('election_id', '')
    new_status  = data.get('status', 'OPEN')

    election = next((e for e in ELECTIONS if e['id'] == election_id), None)
    if not election:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    election['status'] = new_status
    log_action(user['name'], f'Election {election_id} → {new_status}')
    return jsonify({'success': True, 'status': new_status})

# Admin: Delete election
@app.route('/admin/delete-election', methods=['POST'])
def admin_delete_election():
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data        = request.get_json() or {}
    election_id = data.get('election_id', '')
    global ELECTIONS
    before = len(ELECTIONS)
    ELECTIONS = [e for e in ELECTIONS if e['id'] != election_id]
    if len(ELECTIONS) < before:
        CANDIDATES.pop(election_id, None)
        log_action(user['name'], f'Deleted Election {election_id}')
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Not found'}), 404

# Admin: Get all candidates for an election (for the dynamic form)
@app.route('/admin/candidates/<election_id>')
def admin_candidates(election_id):
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'candidates': CANDIDATES.get(election_id, [])})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
