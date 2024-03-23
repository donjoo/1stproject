document.getElementById("productSelect").addEventListener("change", function() {
    const productId = this.value;
    fetch(`/get_variants/?product_id=${productId}`)
        .then(response => response.json())
        .then(data => {
            const variantsSelect = document.getElementById("variantsSelect");
            variantsSelect.innerHTML = ""; // Clear existing options
            data.variants.forEach(variant => {
                const option = new Option(variant.size, variant.id);
                variantsSelect.add(option);
            });
        });
});
