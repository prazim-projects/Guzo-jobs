import {ApolloClient, InMemoryCache, HttpLink} from '@apollo/client/core';
import { DefaultApolloClient } from '@vue/apollo-composable';
import type { App } from 'vue';


const httpLink = new HttpLink({
    uri: import.meta.env.VITE_GRAPHQL_HTTP || 'http://localhost:8000/graphql/',
    credentials: 'include',
    
});

const cache = new InMemoryCache();

export const apolloClient = new ApolloClient({
    link: httpLink,
    cache: cache,
});

export const apolloPlugin = {
    install(app: App) {
        app.provide(DefaultApolloClient, apolloClient);
    }
}