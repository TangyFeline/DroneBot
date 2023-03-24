function switchTab(link){		
	document.getElementById('activeLi').id =""
	link.id = "activeLi"
	activetab = document.querySelector('.activetab')
	console.log(activetab)
	activetab.classList.remove('activetab')
	swapto = link.getAttribute('for')	
	document.getElementById(swapto).classList.add('activetab')
}
function assign_mantra()
{
	mantra = document.querySelector("#mymantra").value;
	console.log(mantra)
}
function postForm(data){
	fetch('/set_values', {
	  method: 'POST',
	  headers: {
	    'Content-Type': 'application/json'
	  },
	  body: JSON.stringify(data)
	})
  .then(response => response.text())
  .then(result => {
    console.log(result);
  });
}

url = window.location.href
my_key = url.substring(url.lastIndexOf('/') + 1);
forms = document.querySelectorAll('form');
for (let form of forms){
	form.addEventListener('submit', function(event){		
		event.preventDefault();
		parent = event.target.parentNode;
		type = parent.id
		console.log(type)
		dataElements = form.querySelectorAll('select,input,textarea')
		data = {'key':my_key, 'type':type}
		console.log(dataElements)
		console.log(form)
		for (dataElement of dataElements){
			if (dataElement.type == "checkbox"){
				data[dataElement.name] = dataElement.checked;
			}
			else{
				data[dataElement.name] = dataElement.value;
			}
		}
		console.log(data)
		postForm(data)
	});
}