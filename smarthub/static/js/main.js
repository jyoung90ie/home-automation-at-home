const createAlertElement = (alertMessage, alertType) => {
    if (!alertMessage) return;

    if (!alertType) {
        alertType = "alert-success"
    }
    const mainBodyContainer = document.querySelector("body > div.container");

    const alertContainerHTML = '<div class="alert ' + alertType + ' alert-dismissible fade show" role="alert">' +
        alertMessage +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
        '</div>';

    alertElement = $(alertContainerHTML);

    // remove any existing alerts before creating new one
    if ($("." + alertType).length > 0) {
        $("." + alertType).remove();
    }

    $(mainBodyContainer).prepend(alertElement);

    clearTimeout();
    setTimeout(() => $(alertElement).remove(), 5000);
}

const deviceStateClass = ".change-device-state"


if ($(deviceStateClass).length > 0) {

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    $(deviceStateClass).on("click", (event) => {
        // event.preventDefault();
        url = event.currentTarget.action

        const request = new Request(
            url,
            { headers: { "X-CSRFToken": csrftoken } }

        );

        fetch(request, {
            method: "POST",
            mode: "same-origin"
        })
            .then(response => response.json())
            .then(response => {

                if (response.status == "error") {
                    status = "alert-danger"
                } else {
                    status = "alert-success"
                }

                createAlertElement(response.message, status);
            })

        return false;
    })
}


