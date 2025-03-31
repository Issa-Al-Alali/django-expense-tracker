// Open and close modals
const addExpenseModal = document.getElementById("add-expense-modal");
const editExpenseModal = document.getElementById("edit-expense-modal");
const addExpenseBtn = document.getElementById("add-expense-btn");
const closeAddExpense = document.getElementById("close-add-expense");
const closeEditExpense = document.getElementById("close-edit-expense");

addExpenseBtn.onclick = () => addExpenseModal.style.display = "block";
closeAddExpense.onclick = () => addExpenseModal.style.display = "none";
closeEditExpense.onclick = () => editExpenseModal.style.display = "none";

window.onclick = (event) => {
    if (event.target === addExpenseModal) addExpenseModal.style.display = "none";
    if (event.target === editExpenseModal) editExpenseModal.style.display = "none";
};

// Fetch and display expenses
const fetchExpenses = async () => {
    const userId = "USER_ID"; // Replace with the actual user ID
    const year = document.getElementById("year").value;
    const month = document.getElementById("month").value;
    const categoryName = document.getElementById("category_name").value;

    let url = `/expenses/${userId}/?`;
    if (year) url += `year=${year}&`;
    if (month) url += `month=${month}&`;
    if (categoryName) url += `category_name=${categoryName}&`;

    const response = await fetch(url);
    const expenses = await response.json();

    const tableBody = document.getElementById("expenses-table-body");
    tableBody.innerHTML = "";

    expenses.forEach(expense => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${expense.amount}</td>
            <td>${expense.description}</td>
            <td>${expense.category}</td>
            <td>${expense.expense_date}</td>
            <td>${expense.location}</td>
            <td>
                <button onclick="openEditModal('${expense.id}')">Edit</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
};

// Open edit modal with expense data
const openEditModal = async (expenseId) => {
    const response = await fetch(`/expenses/update/${expenseId}/`);
    const expense = await response.json();

    document.getElementById("edit-expense-id").value = expense.id;
    document.getElementById("edit-budget").value = expense.amount;
    document.getElementById("edit-description").value = expense.description;
    document.getElementById("edit-category").value = expense.category;
    document.getElementById("edit-date").value = expense.expense_date;
    document.getElementById("edit-location").value = expense.location;

    editExpenseModal.style.display = "block";
};

// Add expense
document.getElementById("add-expense-form").onsubmit = async (event) => {
    event.preventDefault();

    const userId = "USER_ID"; // Replace with the actual user ID
    const categoryName = document.getElementById("add-category").value;

    const formData = new FormData(event.target);
    const response = await fetch(`/expenses/add/${userId}/${categoryName}/`, {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(formData)),
        headers: { "Content-Type": "application/json" },
    });

    if (response.ok) {
        addExpenseModal.style.display = "none";
        fetchExpenses();
    }
};

// Edit expense
document.getElementById("edit-expense-form").onsubmit = async (event) => {
    event.preventDefault();

    const expenseId = document.getElementById("edit-expense-id").value;
    const formData = new FormData(event.target);

    const response = await fetch(`/expenses/update/${expenseId}/`, {
        method: "PUT",
        body: JSON.stringify(Object.fromEntries(formData)),
        headers: { "Content-Type": "application/json" },
    });

    if (response.ok) {
        editExpenseModal.style.display = "none";
        fetchExpenses();
    }
};

// Fetch expenses on page load
fetchExpenses();