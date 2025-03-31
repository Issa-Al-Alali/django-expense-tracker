document.addEventListener("DOMContentLoaded", function () {
    const incomeList = document.getElementById("income-list");
    if (incomeList) {
        fetch("/incomes/", {
            headers: {
                Authorization: "Token YOUR_TOKEN_HERE",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                data.forEach((income) => {
                    const li = document.createElement("li");
                    li.textContent = `${income.budget_amount} - ${income.created_at}`;
                    incomeList.appendChild(li);
                });
            })
            .catch((error) => {
                console.error("Error fetching incomes:", error);
            });
    }
});