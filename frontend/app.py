import streamlit as st
import requests

BACKEND_URL = "https://ecommerce-system-4od2.onrender.com/"
IMAGE_NOT_AVAILABLE_URL = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "success_toast" in st.session_state:
    st.toast(st.session_state.success_toast)
    del st.session_state.success_toast

if not st.session_state.logged_in:
    st.title("Ecommerce system - Login")
    st.write("Please enter your username and password")
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    if submit_button:
        if username and password:
            data = {
                "username": username,
                "password": password
            }
            response = requests.post(f"{BACKEND_URL}/api/login", json=data)

            if response.status_code == 200:
                result = response.json()
                st.session_state.logged_in = True
                st.session_state.access_token = result.get("access_token")
                st.session_state.user_role = result.get("role_identity")
                st.success("Login successfully! Loading...")
                st.rerun()

            elif response.status_code in [401, 500]:
                result = response.json()
                st.error(result.get("detail", "Login failed! Try again."))
            else:
                st.error(f"Server Error! Status code: {response.status_code}")

        else:
            st.warning("Please enter username and password!")

    st.write("New to our system? Create an account below!")
    
    with st.form("register_form", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            register_button = st.form_submit_button("Register")

    if register_button:
        if new_username and new_password:
            data = {
                "username": new_username,
                "password": new_password
            }
            response = requests.post(f"{BACKEND_URL}/api/register", json=data)

            if response.status_code == 201:
                st.success("Account created! You can login now.")

            elif response.status_code in [400, 500]:
                result = response.json()
                st.error(result.get("detail", "Register failed! Try again"))
            else:
                st.error(f"Server Error! Status code: {response.status_code}")

        else:
            st.warning("Please enter username and password!")

else:
    with st.sidebar:
        st.title("Account info")
        st.write(f"Your role: `{st.session_state.user_role}`")

        if st.button("Logout"):
            headers = {
                "Authorization": f"Bearer {st.session_state.access_token}"
            }
            response = requests.post(f"{BACKEND_URL}/api/logout", headers=headers)
            st.session_state.logged_in = False
            st.session_state.access_token = None
            st.session_state.user_role = None
            st.success("Logout successfully!")
            st.rerun()

        if st.session_state.user_role == "admin":
            st.title("Add New Product")

            with st.form("create_product_form", clear_on_submit=True):
                title = st.text_input("Product Title")
                description = st.text_area("Description")
                original_price = st.number_input("Original Price", min_value=1.0, format="%.2f")
                flash_price = st.number_input("Flash Sale Price", min_value=1.0, format="%.2f")
                stock = st.number_input("Stock Quantity", min_value=1, step=1)
                uploaded_file = st.file_uploader("Upload Product Image", type=["png", "jpg", "jpeg"])
                
                submit_product = st.form_submit_button("Upload Product")

                if submit_product:
                    if title and description:
                        product_data = {
                            "title": title,
                            "description": description,
                            "original_price": str(original_price),
                            "flash_price": str(flash_price),
                            "stock": str(stock),
                        }
                        file_data = None
                        if uploaded_file is not None:
                            file_data = {
                                "photo": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                            }
                        headers = {
                            "Authorization": f"Bearer {st.session_state.access_token}"
                        }
                        response = requests.post(f"{BACKEND_URL}/api/products",
                        data=product_data,
                        files=file_data,
                        headers=headers
                        )

                        if response.status_code == 201:
                            st.success("Product uploaded successfully!")
                        else:
                            st.error("creation failed! Try again.")
                    else:
                        st.warning("Please fill in the required fields.")

    st.title("Welcome to the Minimalist Ecommerce Mall")
    st.subheader("Shopping Zone")

    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}"
    }

    response = requests.get(f"{BACKEND_URL}/api/products", headers=headers)

    if response.status_code == 200:
        products = response.json()

        if not products:
            st.info("There are no products available at the moment.")
        else:
            ITEMS_PER_ROW = 2
            for i in range(0, len(products), ITEMS_PER_ROW):
                row_products = products[i : i + ITEMS_PER_ROW]
                cols = st.columns(ITEMS_PER_ROW, gap="large")

                for index, product in enumerate(row_products):
                    with cols[index]:
                            img_url = product.get("photo_url")
                            if img_url:
                                st.html(f"""
                                    <img src="{img_url}" 
                                        style="width:100%; height:220px; object-fit:contain; background-color:#F8FAFC; border-radius:8px;" />
                                """)
                            else:
                                st.html(f"""
                                    <img src="{IMAGE_NOT_AVAILABLE_URL}" 
                                        style="width:100%; height:220px; object-fit:contain; background-color:#F8FAFC; border-radius:8px;" />
                                """)
                            
                            st.subheader(product.get("title", "Untitled Product"))
                            st.caption(product.get("description", "No description available"))
                            
                            st.markdown(f"~~Original Price: ${product.get('original_price'):,.2f}~~")
                            st.markdown(f"Flash Sale Price: :red[${product.get('flash_price'):,.2f}]")
                            
                            stock = product.get("stock", 0)
                            if stock > 0:
                                st.write(f"Remaining Stock: {stock}")
                                if st.button(f"Buy Now", key=f"buy_{product.get('id')}", width="stretch"):
                                    data = {
                                        "quantity": 1,
                                        "product_id": int(product.get('id'))
                                    }
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/orders",
                                        json=data,
                                        headers=headers
                                    )

                                    if response.status_code == 201:
                                        st.session_state.success_toast = f"Purchase successful! Reserved {product.get('title')} for you."
                                        st.rerun()
                                    else:
                                        st.error("order failed! Try again.")
                            else:
                                st.error("Out of Stock!")

                st.write("---")

    elif response.status_code == 401:
            st.error("Login session expired or logged out, please login again!")
            st.session_state.clear()
            st.rerun()
    else:
            st.error(f"Failed to load products. Backend error code: {response.status_code}")
