(function ($) {
    "use strict";

    /*Sale statistics Chart*/
    if ($('#myChart').length) {
        var ctx = document.getElementById('myChart').getContext('2d');
        var chart = new Chart(ctx, {
            // The type of chart we want to create
            type: 'line',
            
            // The data for our dataset
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                        label: 'Sales',
                        tension: 0.3,
                        fill: true,
                        backgroundColor: 'rgba(44, 120, 220, 0.2)',
                        borderColor: 'rgba(44, 120, 220)',
                        data: [18, 17, 4, 3, 2, 20, 25, 31, 25, 22, 20, 9]
                    },
                    {
                        label: 'Visitors',
                        tension: 0.3,
                        fill: true,
                        backgroundColor: 'rgba(4, 209, 130, 0.2)',
                        borderColor: 'rgb(4, 209, 130)',
                        data: [40, 20, 17, 9, 23, 35, 39, 30, 34, 25, 27, 17]
                    },
                    {
                        label: 'Products',
                        tension: 0.3,
                        fill: true,
                        backgroundColor: 'rgba(380, 200, 230, 0.2)',
                        borderColor: 'rgb(380, 200, 230)',
                        data: [30, 10, 27, 19, 33, 15, 19, 20, 24, 15, 37, 6]
                    }

                ]
            },
            options: {
                plugins: {
                legend: {
                    labels: {
                    usePointStyle: true,
                    },
                }
                }
            }
        });
    } //End if

    /*Sale statistics Chart*/
    if ($('#myChart2').length) {
        var ctx = document.getElementById("myChart2");
        var myChart = new Chart(ctx, {
            type: 'bar',
            data: {
            labels: ["900", "1200", "1400", "1600"],
            datasets: [
                {
                    label: "US",
                    backgroundColor: "#5897fb",
                    barThickness:10,
                    data: [233,321,783,900]
                }, 
                {
                    label: "Europe",
                    backgroundColor: "#7bcf86",
                    barThickness:10,
                    data: [408,547,675,734]
                },
                {
                    label: "Asian",
                    backgroundColor: "#ff9076",
                    barThickness:10,
                    data: [208,447,575,634]
                },
                {
                    label: "Africa",
                    backgroundColor: "#d595e5",
                    barThickness:10,
                    data: [123,345,122,302]
                },
            ]
            },
            options: {
                plugins: {
                    legend: {
                        labels: {
                        usePointStyle: true,
                        },
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } //end if
    
})(jQuery);


// addd to cart

// $(".add-to-cart-btn").on("click",function(){
//     let quantity = $("#product-quantity").val()
//     let product_title = $(".product-title").val()
//     let product_id = $(".product-id").val()
//     let product_price = $(".current-product-price").text()
//     let this_val = $(this)



//      console.log("Quantity:",quantity);
//      console.log("title:",product_title);
//      console.log("Price:",product_price);
//      console.log("ID:",product_id);
//      console.log("Curent Element:",this_val);


    //  $.ajax({
    //     url:'/add-to-cart',
    //     data:{
    //         'id':product_id,
    //         'qty':quantity,
    //         'title':product_title,
    //         'price':product_price,

    //     },
    //     daaType:'json',
    //     beforeSend:function(){
    //         console.log("adding Product to Cart.....");
    //     },
    //     success: function(res){
    //         this_val.html("Items added to cart")
    //         console.log("added product to cart")
    //     }
    //  })

    // })

$(document).ready(function() {
$(".add-to-cart-btn").on("click",function(){
    
    
    let this_val = $(this)
    let index=this_val.attr("data-index")

    let quantity = $(".product-quantity-" + index).val()
    let product_title = $(".product-title-" + index).val()
    let product_id = $(".product-id-" + index).val()
    let product_price = $(".current-product-price-" + index).text()

    let product_pid = $(".product-pid-" + index).val()
    let product_image=$(".product-image-" + index).val()

     console.log("Quantity:",quantity);
     console.log("title:",product_title);
     console.log("Price:",product_price);
     console.log("ID:",product_id);
     console.log("PID:",product_pid);
     console.log("Image:",product_image);
     console.log("Index:",index);
     console.log("Curent Element:",this_val);


     $.ajax({
        url:'/add-to-cart',
        data:{
            'id':product_id,
            'pid':product_pid,
            'image':product_image,
            'qty':quantity,
            'title':product_title,
            'price':product_price,

        },
        dataType:'json',
        beforeSend:function(){
            console.log("adding Product to Cart.....");
        },
        success: function(res){
            this_val.html("Item added to cart")
            console.log("added product to cart")
            $(".cart-items-count").text(response.totalcartitems)
        }
     })

    })



$(".delete-product").on("click",function(){
        
    let product_id = $(this).attr("data-product")
    let this_val = $(this)
    
    console.log("PRoduct ID:", product_id);
    
    $.ajax({
  
        url: "/delete-from-cart",
        data: {
            "id":product_id
        },
        dataType:"json",
        beforeSend: function(){
            this_val.hide()
        },
        success: function(response){
            console.log(response);
            this_val.show()
            $(".cart-items-count").text(response.totalcartitems)
            $("#cart-list").html(response.data)
        },
    })
        

    


})

// $(".delete-product").on("click", function () {
//     let product_id = $(this).attr("data-product");
//     let this_val = $(this);

//     console.log("Product ID:", product_id);

//     $.ajax({
//         url: "/delete-from-cart",
//         data: {
//             "id": product_id
//         },
//         dataType: "json",
//         beforeSend: function () {
//             this_val.hide();
//         },
//         success: function (response) {
//             this_val.show();
//             $(".cart-items-count").text(response.totalcartitems);
//             $("#cart-list").html(response.data);
//         },
//         error: function (xhr, status, error) {
//             console.error(xhr.responseText);
//         }
//     });
// });





})