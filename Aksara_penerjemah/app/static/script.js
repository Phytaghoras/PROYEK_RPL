function searchTable() {
    var input, filter, table, tr, td, i, j, txtValue;
    input = document.getElementById("searchInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("aksaraTable");
    tr = table.getElementsByTagName("tr");

    for (i = 1; i < tr.length; i++) {
        tr[i].style.display = "none";
        td = tr[i].getElementsByTagName("td");
        for (j = 0; j < td.length; j++) {
            if (td[j]) {
                txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                    break;
                }
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const element = document.getElementById('variantSelect');
    const choices = new Choices(element, {
        removeItemButton: true,
        placeholderValue: 'Pilih varian...',
        searchEnabled: true
    });

    function updateTableHeader() {
        const select = document.getElementById("variantSelect");
        const selectedOptions = Array.from(select.selectedOptions);
        const headerRow = document.getElementById("tableHeader");

        headerRow.innerHTML = '<th>No</th>';
        selectedOptions.forEach(option => {
            const th = document.createElement("th");
            th.textContent = option.value;
            headerRow.appendChild(th);
        });

        updateTableContent(selectedOptions.length);
    }

    function updateTableContent(columnsCount) {
        const tableBody = document.querySelector("#variantTable tbody");
        const rows = tableBody.getElementsByTagName("tr");

        for (let row of rows) {
            row.innerHTML = `<td>${row.cells[0].textContent}</td>`;
            for (let i = 0; i < columnsCount; i++) {
                const td = document.createElement("td");
                td.textContent = "--";
                row.appendChild(td);
            }
        }
    }

    element.addEventListener('change', updateTableHeader);
});


