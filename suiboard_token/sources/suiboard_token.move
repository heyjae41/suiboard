module suiboard_token::suiboard_token {
    use sui::coin::{Self, Coin, TreasuryCap};
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};
    use sui::url;
    use std::option;

    /// The one-time witness for this module.
    struct SUIBOARD_TOKEN has drop {}

    /// Register the SUIBOARD_TOKEN currency to acquire its `TreasuryCap`.
    fun init(witness: SUIBOARD_TOKEN, ctx: &mut TxContext) {
        let (treasury_cap, metadata) = coin::create_currency(
            witness,
            // Decimals for the token
            2, // Example: 2 decimal places
            // Symbol for the token
            b"BOARD",
            // Name for the token
            b"Suiboard Token",
            // Description for the token
            b"Token for Suiboard project rewards and activities",
            // Optional URL for the token icon
            option::some(url::new_unsafe_from_bytes(b"https://marketmaker.store/img/logo.png")), // Placeholder URL
            ctx
        );
        // Freeze the metadata object, making it immutable
        transfer::public_freeze_object(metadata);
        // Transfer the `TreasuryCap` to the module publisher
        transfer::public_transfer(treasury_cap, tx_context::sender(ctx));
    }

    /// Mint new coins.
    /// Requires the `TreasuryCap` capability to authorize the minting.
    public entry fun mint(
        treasury_cap: &mut TreasuryCap<SUIBOARD_TOKEN>,
        amount: u64,
        recipient: address,
        ctx: &mut TxContext
    ) {
        coin::mint_and_transfer(treasury_cap, amount, recipient, ctx);
    }

    /// Burn coins.
    /// Requires the `TreasuryCap` capability to authorize the burning.
    public entry fun burn(
        treasury_cap: &mut TreasuryCap<SUIBOARD_TOKEN>,
        coin: Coin<SUIBOARD_TOKEN>
    ) {
        coin::burn(treasury_cap, coin);
    }
}
