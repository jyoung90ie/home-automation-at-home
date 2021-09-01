// var deviceList = document.getElementById('device-list')
// if (deviceList) {
//     var tooltip = new bootstrap.Tooltip(deviceList, { animation: true })
// }


// device comms


const deviceStateClass = ".change-device-state"


if ($(deviceStateClass).length > 0) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    $(deviceStateClass).on("click", (event) => {
        // event.preventDefault();
        url = event.target.baseURI
        console.log("url", url)
        // var url = event.target.parent().action
        // console.log("url", url)
        return false;
    })
}


// const makeRequest = new Request(

// )