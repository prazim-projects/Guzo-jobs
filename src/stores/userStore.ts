import { defineStore } from 'pinia'
import { ref } from 'vue'
import { gql } from '@apollo/client/core'
import { useApolloClient } from '@vue/apollo-composable'
import { useRouter } from 'vue-router'


export const useAuthStore = defineStore('auth', () => {
    let savedUser = null
    let savedToken = localStorage.getItem('authToken')
    try {
        savedUser = JSON.parse(localStorage.getItem('user') || 'null')
        const payload = JSON.parse(atob((savedToken || '').split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
        if (!savedUser?.id || !Number.isFinite(payload.exp) || payload.exp * 1000 <= Date.now()) throw new Error('Expired session')
    } catch {
        savedUser = null
        savedToken = null
        localStorage.removeItem('authToken')
        localStorage.removeItem('user')
    }
    const token = ref<string | null>(savedToken)
    const user = ref(savedUser)
    const isAuthenticated = ref(!!savedToken)
  
    const { client } = useApolloClient()

    function acceptSession(jwtToken: string, userData: Record<string, unknown>) {
        if (!jwtToken || !userData?.id) throw new Error('Invalid authentication response')
        token.value = jwtToken
        user.value = userData
        localStorage.setItem('authToken', jwtToken)
        localStorage.setItem('user', JSON.stringify(userData))
        isAuthenticated.value = true
        void client.clearStore()
    }

  // Login Mutation
    async function login(username: string, password: string) {
        const LOGIN_MUTATION = gql`
        mutation Login($username: String!, $password: String!) {
            tokenAuth(username: $username, password: $password) {
            token
            payload
            user {
                id
                bio
                email
                phoneNumber
                username
                }
            }
        }
        `
        try {
        const { data } = await client.mutate({
            mutation: LOGIN_MUTATION,
            variables: { username, password }
        })

        const jwtToken = data.tokenAuth.token
        const userData = data.tokenAuth.user
        if (!jwtToken || !userData) throw new Error('invalid_credentials')
        acceptSession(jwtToken, userData)
        } catch (error) {
        console.error('Login failed:', error)
        throw error  // show alert
        }
  }

  // Register Mutation
  async function register(username: string, phoneNumber: string, password: string, confirmPassword: string, email = '') {
    const REGISTER_MUTATION = gql`
      mutation RegisterUser($username: String!, $phoneNumber: String!, $password: String!, $confirmPassword: String!, $email: String) {
        RegisterUser(username: $username, phoneNumber: $phoneNumber, password: $password, confirmPassword: $confirmPassword, email: $email) {
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
        variables: { username, phoneNumber, password, confirmPassword, email }
      })

      const jwtToken = data.RegisterUser.token 
      const userData = data.RegisterUser.user
      if (!jwtToken || !userData) throw new Error('request_failed')
      acceptSession(jwtToken, userData)
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
    localStorage.removeItem('user')
    isAuthenticated.value = false
    void client.clearStore()
    router.push('/home')
  }

  return { token, user, isAuthenticated, login, register, acceptSession, logout }
})
