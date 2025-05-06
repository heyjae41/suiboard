module suiboard_storage::suiboard_storage {
    use sui::object::{Self, ID, UID};
    use sui::dynamic_field::{Self as df};
    use sui::tx_context::{Self, TxContext};
    use std::string::{Self, String};
    use sui::transfer;
    use sui::clock::{Self, Clock}; // Import Clock

    /// Represents a single post stored on-chain.
    public struct Post has store, copy, drop { // Added public
        id: u64, // Simple ID for the post within this storage
        author: address,
        title: String,
        content: String,
        timestamp: u64,
    }

    /// Shared object acting as the central storage for all posts.
    /// Posts will be stored as dynamic fields on this object.
    public struct BoardStorage has key { // Added public
        id: UID,
        post_counter: u64, // Counter to generate unique post IDs
    }

    /// Creates the initial BoardStorage object during module initialization.
    fun init(ctx: &mut TxContext) {
        transfer::transfer(
            BoardStorage {
                id: object::new(ctx),
                post_counter: 0,
            },
            tx_context::sender(ctx) // Transfer to sender initially
        );
    }

    /// Adds a new post to the BoardStorage.
    /// The post is stored as a dynamic field, keyed by its unique ID.
    public entry fun add_post(
        storage: &mut BoardStorage,
        title: vector<u8>,
        content: vector<u8>,
        clock: &Clock, // Pass Clock object
        ctx: &mut TxContext
    ) {
        let post_id = storage.post_counter;
        let sender = tx_context::sender(ctx);
        let timestamp = clock::timestamp_ms(clock); // Use clock::timestamp_ms

        let post = Post {
            id: post_id,
            author: sender,
            title: string::utf8(title),
            content: string::utf8(content),
            timestamp: timestamp,
        };

        // Add the post as a dynamic field to the storage object
        // Key: post_id (u64), Value: Post struct
        df::add(&mut storage.id, post_id, post);

        // Increment the post counter for the next post
        storage.post_counter = post_id + 1;
    }

    /// Retrieves a post by its ID.
    /// Borrows the dynamic field immutably.
    public fun get_post(storage: &BoardStorage, post_id: u64): &Post {
        df::borrow(&storage.id, post_id)
    }

    /// Retrieves a post mutably by its ID (example, might not be needed).
    /// Borrows the dynamic field mutably.
    public fun get_post_mut(storage: &mut BoardStorage, post_id: u64): &mut Post {
        df::borrow_mut(&mut storage.id, post_id)
    }

    /// Removes a post by its ID (example, requires author check).
    /// Removes the dynamic field.
    public fun remove_post(storage: &mut BoardStorage, post_id: u64, ctx: &TxContext) {
        let post_ref: &Post = df::borrow(&storage.id, post_id);
        assert!(post_ref.author == tx_context::sender(ctx), 1); // Only author can remove
        let _post: Post = df::remove(&mut storage.id, post_id);
        // The removed Post object is dropped here as it has `drop` ability.
    }

}
