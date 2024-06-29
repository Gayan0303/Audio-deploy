from flask import Flask, render_template, request, jsonify
import numpy as np
import pyaudio
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

freqs = [125.0, 250.0, 500.0, 1000.0, 2000.0, 3000.0, 4000.0, 6000.0, 8000.0]
volume = 0.1
duration = 1.0  # in seconds
fs = 44100  # sampling rate

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

left_points = []
left_volumes = []
right_points = []
right_volumes = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play_freq', methods=['POST'])
def play_freq():
    global volume

    ear = request.json['ear']
    freq = request.json['freq']

    samples = (np.sin(2 * np.pi * np.arange(fs * duration) * freq / fs)).astype(np.float32)
    stream.write(volume * samples)

    return jsonify(success=True)

@app.route('/submit_response', methods=['POST'])
def submit_response():
    global volume, left_points, left_volumes, right_points, right_volumes

    ear = request.json['ear']
    freq = request.json['freq']
    audible = request.json['audible']

    if ear == 'left':
        if audible:
            left_points.append(freq)
            left_volumes.append(volume)
        else:
            volume += 0.1
            if volume > 1.0:
                volume = 1.0
        return jsonify(volume=volume)
    elif ear == 'right':
        if audible:
            right_points.append(freq)
            right_volumes.append(volume)
        else:
            volume += 0.1
            if volume > 1.0:
                volume = 1.0
        return jsonify(volume=volume)

@app.route('/plot')
def plot():
    img = io.BytesIO()
    plt.figure(figsize=(10, 6))
    if left_points and left_volumes:
        plt.plot(left_points, left_volumes, 'bo-', markersize=5, label='left ear')
    if right_points and right_volumes:
        plt.plot(right_points, right_volumes, 'ro-', markersize=5, label='right ear')
    plt.gca().invert_yaxis()
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Volume (in dB)")
    plt.title("Ear Audiogram")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return render_template('plot.html', plot_url=plot_url)

if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')
