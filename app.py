from flask import Flask, render_template_string, request, session, redirect, url_for, Response
import subprocess
import os

app = Flask(__name__)
app.secret_key = "secure_patching_key_2026"

VALID_USERS = {
    "admin": "admin123",
    "teammate1": "patching2026"
}

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Patching Dashboard</title>
    <style>
        body { font-family: Arial; text-align: center; margin-top: 100px; background-color: #f4f4f9; }
        .login-box { display: inline-block; padding: 30px; background: white; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        input { padding: 10px; margin: 10px 0; width: 80%; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; font-size: 16px; background-color: #0078D4; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #005A9E; }
        .error { color: red; margin-bottom: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Log In</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Log In</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Linux Patching Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 0; background-color: #f4f4f9; }
        .header { display: flex; justify-content: space-between; padding: 15px 50px; background: #333; color: white; align-items: center; }
        .content { margin-top: 50px; }
        .form-group { margin-bottom: 25px; }
        select { padding: 12px; font-size: 16px; margin: 0 15px; border-radius: 4px; min-width: 200px; }
        label { font-size: 18px; font-weight: bold; }
        .run-btn { padding: 15px 30px; font-size: 18px; background-color: #0078D4; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .run-btn:hover { background-color: #005A9E; }
        a.logout { color: #ff4d4d; text-decoration: none; font-weight: bold; }
    </style>
    <script>
        // Define which environments belong to which sites
        const siteConfig = {
            'Uppsala': ['DEV', 'QUAL', 'PROD'],
            'CABDU': ['QUAL', 'PROD'],
            'ALBY': ['QUAL', 'PROD'],
            'AMS': ['DEV', 'QUAL', 'PROD'],
            'EUR': ['DEV', 'QUAL', 'PROD']
        };

        function updateDropdown() {
            const siteSelect = document.getElementById('site');
            const groupSelect = document.getElementById('server_group');
            const selectedSite = siteSelect.value;
            const availableEnvs = siteConfig[selectedSite];
            
            // Clear out the old options
            groupSelect.innerHTML = '';
            
            // Generate new options based on the site configuration
            availableEnvs.forEach(env => {
                // Add APP Servers
                let optApp = document.createElement('option');
                optApp.value = env + '_APP_Servers';
                optApp.text = env + ' App Servers';
                groupSelect.appendChild(optApp);
                
                // Add DB Servers
                let optDb = document.createElement('option');
                optDb.value = env + '_DB_Servers';
                optDb.text = env + ' DB Servers';
                groupSelect.appendChild(optDb);
            });
        }
        
        // Run this once when the page loads to set the initial state
        window.onload = updateDropdown;
    </script>
</head>
<body>
    <div class="header">
        <span>Logged in as: <strong>{{ session['username'] }}</strong></span>
        <a href="/logout" class="logout">Logout</a>
    </div>
    <div class="content">
        <h1>Server Patching Automation</h1>
        
        <form action="/run" method="post">
            <div class="form-group">
                <label for="site">1. Select Site:</label>
                <!-- Added onchange to trigger the JavaScript function -->
                <select name="site" id="site" onchange="updateDropdown()">
                    <option value="Uppsala">Uppsala</option>
                    <option value="CABDU">CABDU</option>
                    <option value="ALBY">ALBY</option>
                    <option value="AMS">AMS</option>
                    <option value="EUR">EUR</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="server_group">2. Select Environment & Server Type:</label>
                <select name="server_group" id="server_group">
                    <!-- Options are now injected automatically by JavaScript -->
                </select>
            </div>
            
            <button type="submit" class="run-btn">Run Linux Patching</button>
        </form>
    </div>
</body>
</html>
"""

STREAM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Patching Log</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 0; background-color: #f4f4f9; }
        .header { padding: 15px; background: #333; color: white; }
        pre { text-align: left; background: #222; color: #0f0; padding: 20px; width: 80%; margin: 20px auto; border-radius: 8px; height: 600px; overflow-y: scroll; white-space: pre-wrap; font-family: monospace; font-size: 15px; }
        a.back-btn { padding: 12px 25px; background-color: #0078D4; color: white; text-decoration: none; border-radius: 5px; font-size: 16px; display: inline-block; margin-bottom: 20px; }
        a.back-btn:hover { background-color: #005A9E; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Live Patching Execution Log (Target: {{ target }})</h2>
    </div>
    <pre id="logOutput">Initializing Ansible Playbook...\n</pre>
    <a href="/" class="back-btn">Go Back to Dashboard</a>

    <script>
        var target = "{{ target }}";
        var logElement = document.getElementById('logOutput');
        var source = new EventSource('/stream/' + target);

        source.onmessage = function(event) {
            logElement.innerHTML += event.data + "\\n";
            logElement.scrollTop = logElement.scrollHeight; 
        };

        source.onerror = function(event) {
            source.close();
            logElement.innerHTML += "\\n[Execution Complete]";
        };
    </script>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user in VALID_USERS and VALID_USERS[user] == pw:
            session['username'] = user
            return redirect(url_for('home'))
        else:
            error = "Invalid username or password"
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML)

@app.route('/run', methods=['POST'])
def run_playbook():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    site = request.form.get('site')
    server_group = request.form.get('server_group')
    
    target = f"{site}_{server_group}"
        
    return render_template_string(STREAM_HTML, target=target)

@app.route('/stream/<target>')
def stream(target):
    if 'username' not in session:
        return "Unauthorized", 401

    def generate():
        cmd = ["ansible-playbook", "-i", "inventory", "--limit", target, "command.yml"]
        env = os.environ.copy()
        env["ANSIBLE_FORCE_COLOR"] = "0"
        env["PYTHONUNBUFFERED"] = "1"
        env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
        env["ANSIBLE_TIMEOUT"] = "10"
        
        try:
            process = subprocess.Popen(
                cmd, 
                cwd="/home/azureuser/ansible", 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1,
                env=env
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    yield f"data: {line.rstrip()}\n\n"
                
            process.stdout.close()
            process.wait()
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)