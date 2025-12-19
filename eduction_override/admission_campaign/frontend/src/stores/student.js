import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createResource } from 'frappe-ui'

export const studentStore = defineStore('education-student', () => {
  const studentInfo = ref({})
  const currentProgram = ref({})
  const studentGroups = ref([])

  const student = createResource({
    url: 'education.education.api.get_student_info',
    onSuccess(info) {
      // Allow access even if student doesn't exist yet (awaiting admin review)
      // Only redirect if info is completely null/undefined
      if (!info) {
        window.location.href = '/app'
        return
      }
      
      // Handle minimal student info (when student record doesn't exist yet)
      if (!info.name) {
        // Student not created yet, but allow portal access with minimal info
        console.log('Student record not found, using minimal info for portal access')
      }
      
      currentProgram.value = info.current_program || null
      // remove current_program from info
      delete info.current_program
      studentGroups.value = info.student_groups || []
      delete info.student_groups
      studentInfo.value = info
    },
    onError(err) {
      console.error(err)
      // Don't redirect on error, allow portal access
    },
  })

  // const s = createDocumentResource({
  // 	doctype:"Student",
  // 	whitelist: {
  // 		'get_student_info': get_student_info
  // 	}
  // })

  function getStudentInfo() {
    return studentInfo
  }
  function getCurrentProgram() {
    return currentProgram
  }

  function getStudentGroups() {
    return studentGroups
  }

  return {
    student,
    studentInfo,
    currentProgram,
    studentGroups,
    getStudentInfo,
    getCurrentProgram,
    getStudentGroups,
  }
})
