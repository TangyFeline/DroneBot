from quart import Quart, render_template, send_from_directory

app = Quart(__name__)
app.template_folder = 'templates'

@app.route('/')
async def hello():
    return 'zxcv'

@app.route("/<path:key>")
async def control_panel(key):
	template = await render_template('control.html',key=key)
	return template

@app.route('/style.css')
async def return_style():
    file = await send_from_directory('static', 'style.css')
    return file

# @app.route('/reset.css')
# def return_reset_style():
#     return send_from_directory('static', 'reset.css')

# @app.route('/script.js')
# def return_script():
#     return send_from_directory('static', 'script.js')

# @app.route('/set_values', methods=['POST'])
# def set_values():
# 	print(request.get_json())
# 	return 'okay'

if __name__ == "__main__":
	app.run()