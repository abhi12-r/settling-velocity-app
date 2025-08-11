from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io

app = Flask(__name__)
last_iterations = None  # store last calculation for download

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    global last_iterations
    data = request.json
    g = float(data.get('g', 9.81))
    d_p = float(data.get('d_p', 0.0006))
    SG = float(data.get('SG', 2.65))
    rho_w = float(data.get('rho_w', 998.8))
    mu = float(data.get('mu', 0.001002))
    v_t = float(data.get('v_t', 0.1))

    rho_p = SG * rho_w
    iteration = 0
    prev_Re = None
    iterations_list = []

    while True:
        Re = (rho_w * v_t * d_p) / mu
        if Re < 0.1:
            Cd = 24 / Re
        elif Re <= 1000:
            Cd = (24.0 / Re) + (3.0 / (Re ** 0.5)) + 0.34
        else:
            Cd = 0.44

        v_t_new = ((4 * (rho_p - rho_w) * g * d_p) / (3 * rho_w * Cd)) ** 0.5
        iteration += 1

        iterations_list.append({
            "Iteration": iteration,
            "Assumed Vt": round(v_t, 6),
            "Re": round(Re, 6),
            "Cd": round(Cd, 6),
            "New Vt": round(v_t_new, 6)
        })

        if prev_Re is not None and round(Re, 6) == round(prev_Re, 6):
            break

        prev_Re = Re
        v_t = v_t_new

    last_iterations = pd.DataFrame(iterations_list)

    return jsonify({
        "velocity": round(v_t_new, 6),
        "Re": round(Re, 6),
        "iterations": iteration,
        "table": iterations_list
    })

@app.route('/download')
def download():
    global last_iterations
    if last_iterations is None:
        return "No calculation yet", 400

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        last_iterations.to_excel(writer, index=False, sheet_name='Iterations')
    output.seek(0)
    return send_file(output,
                     as_attachment=True,
                     download_name='settling_velocity_iterations.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    # keep debug=True while developing locally; Render will run gunicorn in production
    app.run(host='0.0.0.0', port=5000, debug=True)

