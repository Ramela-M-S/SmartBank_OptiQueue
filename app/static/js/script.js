function getToken() {

    let service = document.getElementById("service").value;

    fetch("/user/get-token", {
        method: "POST",
        body: new FormData(document.createElement("form"))
    });

    fetch("/user/get-token", {
        method: "POST",
        body: new URLSearchParams({ service: service })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("token").innerText = data.token;
        document.getElementById("ahead").innerText = data.people_ahead;
        document.getElementById("time").innerText = data.wait_time;
    });
}