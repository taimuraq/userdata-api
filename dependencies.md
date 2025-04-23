graph TD
  subgraph ShopperAPI
    A1["GET /cart/c1"] --> A2["CartService.getCartById"]
    A2 --> A3["RestClientService.getUser"]
    A4["POST /cart"] --> A5["CartService.createCart"]
    A5 --> A6["RestClientService.getUser"]
  end

  A3 --> B1["GET /users/{id}"]
  A6 --> B1
  B1 -->|calls| UserdataAPI["UserdataAPI"]
