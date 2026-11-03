if("serviceWorker" in navigator){
    window.addEventListener("load",()=>{
        navigator.serviceWorker.register("/static/js/service-worker.js")
        .then((registration)=>{
            console.log("✅ Service Worker Registered");
            console.log(registration);
        })
        .catch((error)=>{
            console.error("❌ Service Worker Error:",error);
        });
    });
}

document.addEventListener("DOMContentLoaded",function(){

    const voiceSearchButton=document.getElementById("voiceSearchButton");
    const searchInput=document.getElementById("searchInput");
    const searchForm=document.getElementById("searchForm");

    const hamburgerButton=document.getElementById("hamburgerButton");
    const sideMenu=document.getElementById("sideMenu");
    const menuOverlay=document.getElementById("menuOverlay");
    const closeMenu=document.getElementById("closeMenu");

    const searchSuggestions=document.getElementById("searchSuggestions");

    const alexaButtons=document.querySelectorAll(".alexa-button");

    const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;


    function openSideMenu(){
        if(sideMenu){
            sideMenu.classList.add("active");
        }

        if(menuOverlay){
            menuOverlay.classList.add("active");
        }

        document.body.style.overflow="hidden";
    }


    function closeSideMenu(){
        if(sideMenu){
            sideMenu.classList.remove("active");
        }

        if(menuOverlay){
            menuOverlay.classList.remove("active");
        }

        document.body.style.overflow="";
    }


    if(hamburgerButton){
        hamburgerButton.addEventListener("click",openSideMenu);
    }


    if(closeMenu){
        closeMenu.addEventListener("click",closeSideMenu);
    }


    if(menuOverlay){
        menuOverlay.addEventListener("click",closeSideMenu);
    }


    /* VOICE SEARCH */

    if(SpeechRecognition&&voiceSearchButton&&searchInput){

        const searchRecognition=new SpeechRecognition();

        searchRecognition.lang="en-IN";
        searchRecognition.continuous=false;
        searchRecognition.interimResults=false;


        voiceSearchButton.addEventListener("click",function(){

            try{
                searchRecognition.start();

                voiceSearchButton.innerHTML="🔴";
                voiceSearchButton.classList.add("listening");
                voiceSearchButton.title="Listening...";
            }
            catch(error){
                console.log(error);
            }

        });


        searchRecognition.onresult=function(event){

            const transcript=event.results[0][0].transcript;

            searchInput.value=transcript;

            voiceSearchButton.innerHTML="🎤";
            voiceSearchButton.classList.remove("listening");
            voiceSearchButton.title="Voice Search";

            searchInput.dispatchEvent(new Event("input"));

        };


        searchRecognition.onerror=function(){

            voiceSearchButton.innerHTML="🎤";
            voiceSearchButton.classList.remove("listening");
            voiceSearchButton.title="Voice Search";

            alert("Voice search could not understand your voice. Please try again.");

        };


        searchRecognition.onend=function(){

            voiceSearchButton.innerHTML="🎤";
            voiceSearchButton.classList.remove("listening");
            voiceSearchButton.title="Voice Search";

        };

    }else if(voiceSearchButton){

        voiceSearchButton.addEventListener("click",function(){
            alert("Voice Search is not supported. Please use Google Chrome.");
        });

    }


    /* ALEXA VOICE COMMAND */

    if(SpeechRecognition&&alexaButtons.length>0){

        alexaButtons.forEach(function(alexaButton){

            const alexaRecognition=new SpeechRecognition();

            alexaRecognition.lang="en-IN";
            alexaRecognition.continuous=false;
            alexaRecognition.interimResults=false;


            alexaButton.addEventListener("click",function(){

                try{

                    alexaRecognition.start();

                    alexaButton.innerHTML="🔴 Listening...";
                    alexaButton.classList.add("listening");

                }
                catch(error){
                    console.log(error);
                }

            });


            alexaRecognition.onresult=function(event){

                const command=event.results[0][0].transcript.toLowerCase().trim();

                console.log("Alexa Command:",command);

                resetAlexaButtons();

                handleVoiceCommand(command);

            };


            alexaRecognition.onerror=function(){

                resetAlexaButtons();

                alert("I could not understand the command. Please try again.");

            };


            alexaRecognition.onend=function(){

                resetAlexaButtons();

            };

        });

    }else if(alexaButtons.length>0){

        alexaButtons.forEach(function(button){

            button.addEventListener("click",function(){

                alert("Voice Command is not supported. Please use Google Chrome.");

            });

        });

    }


    function resetAlexaButtons(){

        alexaButtons.forEach(function(button){

            button.innerHTML="🔵 Alexa";
            button.classList.remove("listening");

        });

    }


    /* LIVE SEARCH */

    if(searchInput&&searchSuggestions){

        let searchTimeout;


        searchInput.addEventListener("input",function(){

            const query=this.value.trim();

            clearTimeout(searchTimeout);


            if(query.length===0){

                searchSuggestions.innerHTML="";
                searchSuggestions.style.display="none";

                return;

            }


            searchTimeout=setTimeout(function(){

                fetch(
                    window.liveSearchUrl+
                    "?q="+
                    encodeURIComponent(query)
                )

                .then(function(response){

                    return response.json();

                })

                .then(function(data){

                    let html="";


                    /* CATEGORY RESULTS */

                    if(data.categories&&data.categories.length>0){

                        html+=`
                            <div class="suggestion-heading">
                                Categories
                            </div>
                        `;


                        data.categories.forEach(function(category){

                            html+=`
                                <div class="suggestion-item category-suggestion"
                                data-category="${category}">
                                    📁 ${category}
                                </div>
                            `;

                        });

                    }


                    /* PRODUCT RESULTS */

                    if(data.products&&data.products.length>0){

                        html+=`
                            <div class="suggestion-heading">
                                Products
                            </div>
                        `;


                        data.products.forEach(function(product){

                            html+=`
                                <div class="suggestion-item product-suggestion"
                                data-product-id="${product.id}">
                                    🔍 ${product.name}
                                </div>
                            `;

                        });

                    }


                    if(html===""){

                        html=`
                            <div class="no-suggestion">
                                No results found
                            </div>
                        `;

                    }


                    searchSuggestions.innerHTML=html;
                    searchSuggestions.style.display="block";


                    document.querySelectorAll(".category-suggestion").forEach(function(item){

                        item.addEventListener("click",function(){

                            const category=this.dataset.category;

                            window.location.href=
                                "/?category="+
                                encodeURIComponent(category)+
                                "#products";

                        });

                    });


                    document.querySelectorAll(".product-suggestion").forEach(function(item){

                        item.addEventListener("click",function(){

                            const productId=this.dataset.productId;

                            window.location.href=
                                "/product/"+
                                productId+
                                "/";

                        });

                    });

                })

                .catch(function(error){

                    console.error("Live Search Error:",error);

                });

            },300);

        });

    }


    /* CLOSE SEARCH SUGGESTIONS */

    document.addEventListener("click",function(event){

        if(!event.target.closest(".search-wrapper")){

            if(searchSuggestions){
                searchSuggestions.style.display="none";
            }

        }

    });


    /* VOICE COMMAND FUNCTION */

    function handleVoiceCommand(command){

        if(!window.voiceUrls){

            alert("Voice navigation is not configured.");

            return;

        }


        if(command.includes("admin dashboard")||command.includes("open dashboard")){

            window.location.href=window.voiceUrls.admin_dashboard;

            return;

        }


        if(command.includes("admin products")||command.includes("open products")||command.includes("product page")){

            window.location.href=window.voiceUrls.admin_products;

            return;

        }


        if(command.includes("admin orders")||command.includes("open orders")||command.includes("order page")){

            window.location.href=window.voiceUrls.admin_orders;

            return;

        }


        if(command.includes("my orders")||command.includes("open my orders")){

            window.location.href=window.voiceUrls.my_orders;

            return;

        }


        if(command.includes("open cart")||command==="cart"){

            window.location.href=window.voiceUrls.cart;

            return;

        }


        if(command.includes("open wishlist")||command==="wishlist"){

            window.location.href=window.voiceUrls.wishlist;

            return;

        }


        if(command.includes("open profile")||command==="profile"){

            window.location.href=window.voiceUrls.profile;

            return;

        }


        if(command.includes("go home")||command.includes("open home")||command==="home"){

            window.location.href=window.voiceUrls.home;

            return;

        }


        alert("Command not recognized: "+command);

    }

});