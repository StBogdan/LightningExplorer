// Code for reading from a file

function handleFileSelect(evt) {
	var files = evt.target.files; // FileList object
  console.log(evt.target.files);
	// files is a FileList of File objects. List some properties.
	var output = [];
	for (var i = 0, f; f = files[i]; i++) {
		var reader = new FileReader();

		// Closure to capture the file information.
		reader.onload = (function (theFile) {
			return function (e) {
				console.log('e readAsText = ', e);
				console.log('e readAsText target = ', e.target);
				try {
					jsonData = JSON.parse(e.target.result);
				} catch (ex) {
					alert('ex when trying to parse json = ' + ex);
				}
			}
		})(f);
		reader.readAsText(f);
	}
}
// document.getElementById('files').addEventListener('change', handleFileSelect, false);
// <input type="file" id="files" name="files[]" multiple />
