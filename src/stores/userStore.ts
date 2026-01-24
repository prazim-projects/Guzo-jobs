import { defineStore } from 'pinia'
import { ref } from 'vue'
import { gql } from '@apollo/client/core'
import { useApolloClient } from '@vue/apollo-composable'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('authToken'))
  const user = ref<{ id: string; username: string; phoneNumber: string } | null>(null)
  const isAuthenticated = ref(!!token.value)

  const { client } = useApolloClient()

  // Login Mutation
  async function login(username: string, password: string) {
    const LOGIN_MUTATION = gql`
      mutation Login($username: String!, $password: String!) {
        tokenAuth(username: $username, password: $password) {
          token
          payload
        }
      }
    `
    try {
      const { data } = await client.mutate({
        mutation: LOGIN_MUTATION,
        variables: { username, password }
      })

      const jwtToken = data.tokenAuth.token
      if (jwtToken) {
        token.value = jwtToken
        localStorage.setItem('authToken', jwtToken)
        isAuthenticated.value = true
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error  // show alert
    }
  }

  // Register Mutation
  async function register(username: string, phoneNumber: string, password: string) {
    const REGISTER_MUTATION = gql`
      mutation RegisterUser($username: String!, $phoneNumber: String!, $password: String!) {
        RegisterUser(username: $username, phoneNumber: $phoneNumber, password: $password) {
          token
          user {
            id
            username
            phoneNumber
          }
        }
      }
    `
    try {
      const { data } = await client.mutate({
        mutation: REGISTER_MUTATION,
        variables: { username, phoneNumber, password }
      })

      const jwtToken = data.RegisterUser.token 
      if(jwtToken){
        token.value = jwtToken
        user.value = data.RegisterUser.user
        localStorage.setItem('authToken', jwtToken)
        isAuthenticated.value = true

      }
    } catch (error) {
      console.error('Register failed:', error)
      throw error
    }
  }

  const router = useRouter()
  // Logout
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('authToken')
    isAuthenticated.value = false
    router.push('/home')
  }

  return { token, user, isAuthenticated, login, register, logout }
})