from flask import Flask, render_template

app = Flask(__name__)

directions = [
    {"id": "механика", "name": "Механика", "description": "Изучение движения и равновесия.", "formulas": ["F = ma", "W = Fd"], "image": "mech.png"},
    {"id": "электричество", "name": "Электричество", "description": "Изучение зарядов и токов.", "formulas": ["I = U/R", "P = UI"], "image": "elec.png"},
    {"id": "термодинамика", "name": "Термодинамика", "description": "Изучение тепла и энергии.", "formulas": ["Q = mcΔT"], "image": "thermo.png"},
    {"id": "оптика", "name": "Оптика", "description": "Изучение света.", "formulas": ["n = c/v"], "image": "optic.png"},
    {"id": "силы", "name": "Силы", "description": "Сила — векторная величина.", "formulas": ["F = G(m1m2/r²)"], "image": "force.png"},
    {"id": "масса", "name": "Масса", "description": "Масса — мера инерции.", "formulas": ["m = F/a"], "image": "mass.png"}
]


@app.route('/')
def index():
    return render_template('index.html', directions=directions)


@app.route('/direction/<direction_id>')
def direction(direction_id):
    direction = next((d for d in directions if d["id"] == direction_id), None)
    if direction:
        return render_template('direction.html', direction=direction)
    return "Направление не найдено", 404


if __name__ == '__main__':
    app.run(debug=True)