from flask import Flask, jsonify
import random
import time
from flask_cors import CORS
import os

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Traffic conditions for each side (in terms of vehicle count and density)
sides = ['North', 'South', 'East', 'West']

# Vehicle types (including bikes)
vehicle_types = ['Car', 'Bus', 'Truck', 'Bike']

# Vehicle weights based on type
vehicle_priority = {
    'Car': 1,
    'Bus': 2,
    'Truck': 3,
    'Bike': 0.5
}

# Initialize waiting time history for each side
waiting_time_history = {side: 0 for side in sides}

# Q-Learning parameters
alpha = 0.1  # Learning rate
gamma = 0.9  # Discount factor
epsilon = 0.2  # Exploration factor (for random actions)
q_table = {}  # Q-table to store states and actions

# Traffic pattern adjustments based on time (rush hour simulation)
def get_time_factor():
    current_hour = time.localtime().tm_hour
    if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Rush hour between 7-9 AM and 5-7 PM
        return 1.5  # Longer green time during rush hours
    return 1  # Normal conditions

# Function to generate random traffic data
def generate_traffic_data():
    traffic_data = {}
    for side in sides:
        vehicle_count = random.randint(0, 50)  # Simulating number of vehicles waiting
        vehicle_density = random.randint(0, 100)  # Density of vehicles (percentage)
        vehicle_type = random.choice(vehicle_types)  # Random vehicle type
        
        traffic_data[side] = {
            'vehicle_count': vehicle_count,
            'vehicle_density': vehicle_density,
            'vehicle_type': vehicle_type,
            'priority': vehicle_priority[vehicle_type]  # Assigning vehicle priority
        }
    return traffic_data

# Function to calculate waiting time history
def update_waiting_time_history(signal_decision):
    for side in sides:
        if signal_decision[side]['signal'] == 'Red':
            waiting_time_history[side] += signal_decision[side]['duration']
        else:
            waiting_time_history[side] = 0  # Reset waiting time for sides with green signal

# Function to make traffic signal decision
def traffic_signal_decision(traffic_data):
    # Factor in rush hour or normal hours for signal duration
    time_factor = get_time_factor()

    # Prioritize sides with higher vehicle count and vehicle priority (bus/truck)
    weighted_traffic_data = {side: data['vehicle_count'] * data['priority'] for side, data in traffic_data.items()}
    
    # Calculate the total waiting time for all sides (to avoid starvation)
    total_waiting_time = sum(waiting_time_history.values())
    
    # Find the side with the highest weighted traffic value, while considering waiting time
    max_traffic_side = max(weighted_traffic_data, key=lambda side: weighted_traffic_data[side] + (waiting_time_history[side] / 10))
    
    # Adjust signal durations based on traffic conditions, waiting time, and time of day
    signal_decision = {side: {'signal': 'Red', 'duration': 10} for side in sides}
    signal_decision[max_traffic_side] = {'signal': 'Green', 'duration': int(30 * time_factor)}  # Green light duration
    
    # Update the waiting time history
    update_waiting_time_history(signal_decision)

    # Update Q-table using simple RL mechanism (Q-learning-like update)
    update_q_table(signal_decision)

    return signal_decision

# Simple Q-learning-like update function
def update_q_table(signal_decision):
    global q_table

    # Generate state key from the signal decisions
    state_key = tuple(signal_decision[side]['signal'] for side in sides)
    
    if state_key not in q_table:
        q_table[state_key] = {side: 0 for side in sides}  # Initialize Q-values for each side

    # Reward based on total waiting time (lower waiting time = higher reward)
    reward = -sum(waiting_time_history.values())

    # Update Q-values using Q-learning formula
    for side in sides:
        q_table[state_key][side] += alpha * (reward + gamma * max(q_table.get(state_key, {}).values()) - q_table[state_key][side])

# Exploration vs Exploitation: Choose between random action or learned action (based on epsilon)
def choose_action():
    if random.uniform(0, 1) < epsilon:
        # Exploration: choose a random action
        return random.choice(sides)
    else:
        # Exploitation: choose the best learned action (from Q-table)
        state_key = tuple('Green' if waiting_time_history[side] < 20 else 'Red' for side in sides)
        return max(q_table.get(state_key, {}).items(), key=lambda x: x[1])[0]

@app.route('/')
def home():
    return "Welcome to the Traffic Management System API!"

@app.route('/get-traffic-signal', methods=['GET'])
def get_traffic_signal():
    traffic_data = generate_traffic_data()
    signal_decision = traffic_signal_decision(traffic_data)
    return jsonify(signal_decision)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use the PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)
