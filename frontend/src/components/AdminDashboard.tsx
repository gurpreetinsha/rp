import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import { DatabaseStudio } from './DatabaseStudio';

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'sessions' | 'imports' | 'calculate_publish' | 'amendments' | 'audit' | 'directory' | 'database'>('calculate_publish');
  const [directorySubTab, setDirectorySubTab] = useState<'teachers' | 'students' | 'assignments' | 'enrollments' | 'academic_units'>('teachers');

  // Core Data
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');

  // Directory Data
  const [teachers, setTeachers] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [enrollments, setEnrollments] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);

  // Directory Modals & Forms
  const [showTeacherModal, setShowTeacherModal] = useState(false);
  const [teacherName, setTeacherName] = useState('');
  const [teacherEmail, setTeacherEmail] = useState('');
  const [teacherPassword, setTeacherPassword] = useState('');
  const [teacherEmpId, setTeacherEmpId] = useState('');
  const [teacherDeptId, setTeacherDeptId] = useState('');
  const [teacherDesignation, setTeacherDesignation] = useState('Assistant Professor');

  const [showStudentModal, setShowStudentModal] = useState(false);
  const [studentName, setStudentName] = useState('');
  const [studentEmail, setStudentEmail] = useState('');
  const [studentPassword, setStudentPassword] = useState('');
  const [studentRegNo, setStudentRegNo] = useState('');
  const [studentRollNo, setStudentRollNo] = useState('');
  const [studentProgId, setStudentProgId] = useState('');
  const [studentSem, setStudentSem] = useState(1);

  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignTeacherId, setAssignTeacherId] = useState('');
  const [assignCourseId, setAssignCourseId] = useState('');
  const [assignSessionId, setAssignSessionId] = useState('');

  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollStudentId, setEnrollStudentId] = useState('');
  const [enrollCourseId, setEnrollCourseId] = useState('');
  const [enrollSessionId, setEnrollSessionId] = useState('');

  const [showDeptModal, setShowDeptModal] = useState(false);
  const [newDeptCode, setNewDeptCode] = useState('');
  const [newDeptName, setNewDeptName] = useState('');

  const [showProgModal, setShowProgModal] = useState(false);
  const [newProgDeptId, setNewProgDeptId] = useState('');
  const [newProgCode, setNewProgCode] = useState('');
  const [newProgName, setNewProgName] = useState('');
  const [newProgSemesters, setNewProgSemesters] = useState(8);

  // Calculation & Summary State
  const [summary, setSummary] = useState<any | null>(null);
  const [sessionResults, setSessionResults] = useState<any[]>([]);
  const [officialMarks, setOfficialMarks] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [batches, setBatches] = useState<any[]>([]);

  // Modals & Action States
  const [loading, setLoading] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<{ text: string; type: 'success' | 'danger' } | null>(null);

  // Batch Review state
  const [selectedBatchForReview, setSelectedBatchForReview] = useState<any | null>(null);
  const [batchReviewRows, setBatchReviewRows] = useState<any[]>([]);
  const [loadingBatchRows, setLoadingBatchRows] = useState<boolean>(false);
  const [rejectModalBatch, setRejectModalBatch] = useState<any | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('');

  // Entity Creation Modals
  const [showSessionModal, setShowSessionModal] = useState<boolean>(false);
  const [newSessionName, setNewSessionName] = useState<string>('');
  const [newSessionYear, setNewSessionYear] = useState<string>('2025-2026');
  const [newSessionSem, setNewSessionSem] = useState<number>(1);

  const [showCourseModal, setShowCourseModal] = useState<boolean>(false);
  const [newCourseCode, setNewCourseCode] = useState<string>('');
  const [newCourseName, setNewCourseName] = useState<string>('');
  const [newCourseCredits, setNewCourseCredits] = useState<number>(3.0);
  const [newCoursePassPct, setNewCoursePassPct] = useState<number>(40.0);

  // Amendment modal
  const [selectedMarkForAmend, setSelectedMarkForAmend] = useState<any | null>(null);
  const [amendMarks, setAmendMarks] = useState<number>(0);
  const [amendAbsent, setAmendAbsent] = useState<boolean>(false);
  const [amendReason, setAmendReason] = useState<string>('');
  const [amendmentHistory, setAmendmentHistory] = useState<any[]>([]);

  // Withhold modal
  const [withholdTarget, setWithholdTarget] = useState<any | null>(null);
  const [withholdReason, setWithholdReason] = useState<string>('');

  // Editing Entities State
  const [editingTeacher, setEditingTeacher] = useState<any | null>(null);
  const [editTeacherName, setEditTeacherName] = useState('');
  const [editTeacherEmail, setEditTeacherEmail] = useState('');
  const [editTeacherEmpId, setEditTeacherEmpId] = useState('');
  const [editTeacherDeptId, setEditTeacherDeptId] = useState('');
  const [editTeacherDesignation, setEditTeacherDesignation] = useState('');
  const [editTeacherActive, setEditTeacherActive] = useState(true);
  const [editTeacherPassword, setEditTeacherPassword] = useState('');

  const [editingStudent, setEditingStudent] = useState<any | null>(null);
  const [editStudentName, setEditStudentName] = useState('');
  const [editStudentEmail, setEditStudentEmail] = useState('');
  const [editStudentRegNo, setEditStudentRegNo] = useState('');
  const [editStudentRollNo, setEditStudentRollNo] = useState('');
  const [editStudentProgId, setEditStudentProgId] = useState('');
  const [editStudentSem, setEditStudentSem] = useState(1);
  const [editStudentActive, setEditStudentActive] = useState(true);
  const [editStudentPassword, setEditStudentPassword] = useState('');

  const [editingDept, setEditingDept] = useState<any | null>(null);
  const [editDeptCode, setEditDeptCode] = useState('');
  const [editDeptName, setEditDeptName] = useState('');
  const [editDeptActive, setEditDeptActive] = useState(true);

  const [editingProg, setEditingProg] = useState<any | null>(null);
  const [editProgDeptId, setEditProgDeptId] = useState('');
  const [editProgCode, setEditProgCode] = useState('');
  const [editProgName, setEditProgName] = useState('');
  const [editProgSemesters, setEditProgSemesters] = useState(8);
  const [editProgActive, setEditProgActive] = useState(true);

  const [editingCourse, setEditingCourse] = useState<any | null>(null);
  const [editCourseCode, setEditCourseCode] = useState('');
  const [editCourseName, setEditCourseName] = useState('');
  const [editCourseCredits, setEditCourseCredits] = useState(3.0);
  const [editCoursePassPct, setEditCoursePassPct] = useState(40.0);
  const [editCourseActive, setEditCourseActive] = useState(true);

  const [editingSession, setEditingSession] = useState<any | null>(null);
  const [editSessionName, setEditSessionName] = useState('');
  const [editSessionYear, setEditSessionYear] = useState('');
  const [editSessionSem, setEditSessionSem] = useState(1);
  const [editSessionStatus, setEditSessionStatus] = useState('');

  const showMessage = useCallback((text: string, type: 'success' | 'danger') => {
    setActionMsg({ text, type });
    setTimeout(() => setActionMsg(null), 5000);
  }, []);

  const loadSessions = useCallback(async () => {
    try {
      const sess = await api.getSessions();
      setSessions(sess);
      if (sess.length > 0) {
        setSelectedSessionId((prev) => prev || sess[0].id);
      }
    } catch (err: any) {
      showMessage(err.message || 'Failed to load initial academic data.', 'danger');
    }
  }, [showMessage]);

  const loadSessionData = useCallback(async (sessId: string) => {
    setLoading(true);
    try {
      if (activeTab === 'calculate_publish') {
        const [sum, res] = await Promise.allSettled([
          api.getSessionSummary(sessId),
          api.listSessionResults(sessId),
        ]);
        if (sum.status === 'fulfilled') setSummary(sum.value);
        else setSummary(null);

        if (res.status === 'fulfilled') setSessionResults(res.value);
        else setSessionResults([]);
      } else if (activeTab === 'imports') {
        const batchList = await api.listBatches(sessId);
        setBatches(batchList);
      } else if (activeTab === 'amendments') {
        const marks = await api.getOfficialMarks(sessId);
        setOfficialMarks(marks);
      } else if (activeTab === 'audit') {
        const logs = await api.getAuditLogs(100);
        setAuditLogs(logs);
      } else if (activeTab === 'directory') {
        const [tList, sList, aList, eList, dList, pList, cList] = await Promise.allSettled([
          api.listTeachers(),
          api.listStudents(),
          api.listAssignments(sessId || undefined),
          api.listEnrollments(sessId || undefined),
          api.getDepartments(),
          api.getPrograms(),
          api.getCourses(),
        ]);
        if (tList.status === 'fulfilled') setTeachers(tList.value);
        if (sList.status === 'fulfilled') setStudents(sList.value);
        if (aList.status === 'fulfilled') setAssignments(aList.value);
        if (eList.status === 'fulfilled') setEnrollments(eList.value);
        if (dList.status === 'fulfilled') {
          setDepartments(dList.value);
          if (dList.value.length > 0) {
            setTeacherDeptId((prev) => prev || dList.value[0].id);
            setNewProgDeptId((prev) => prev || dList.value[0].id);
          }
        }
        if (pList.status === 'fulfilled') {
          setPrograms(pList.value);
          if (pList.value.length > 0) {
            setStudentProgId((prev) => prev || pList.value[0].id);
          }
        }
        if (cList.status === 'fulfilled') {
          setCourses(cList.value);
          if (cList.value.length > 0) {
            setAssignCourseId((prev) => prev || cList.value[0].id);
            setEnrollCourseId((prev) => prev || cList.value[0].id);
          }
        }
      }
    } catch {
      // Non-blocking error handling
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (selectedSessionId) {
      loadSessionData(selectedSessionId);
    }
  }, [selectedSessionId, activeTab, loadSessionData]);

  // 1. Session Status Change
  const handleStatusChange = async (newStatus: string) => {
    if (!selectedSessionId) return;
    try {
      await api.updateSessionStatus(selectedSessionId, newStatus);
      showMessage(`Session status transitioned to ${newStatus}`, 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update session status', 'danger');
    }
  };

  // 2. Calculation
  const handleCalculate = async (allowPartial = false) => {
    if (!selectedSessionId) return;
    setLoading(true);
    try {
      const sum = await api.calculateResults(selectedSessionId, allowPartial);
      setSummary(sum);
      showMessage('Academic evaluation completed successfully!', 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Calculation failed.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 3. Publication
  const handlePublish = async () => {
    if (!selectedSessionId) return;
    setLoading(true);
    try {
      const sum = await api.publishSession(selectedSessionId);
      setSummary(sum);
      showMessage('Results published officially! Students can now access their electronic marksheets.', 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Publication failed.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 4. Unpublish Rollback
  const handleUnpublish = async () => {
    const reason = prompt('Please provide administrative reason for unpublishing:');
    if (!reason) return;
    setLoading(true);
    try {
      await api.unpublishSession(selectedSessionId, reason);
      showMessage('Session unpublished and rolled back to CALCULATED status.', 'success');
      loadSessions();
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to unpublish session.', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 5. Withhold Toggle
  const handleToggleWithhold = async () => {
    if (!withholdTarget) return;
    try {
      await api.withholdResult(withholdTarget.id, !withholdTarget.is_withheld, withholdReason);
      showMessage(`Student result ${!withholdTarget.is_withheld ? 'withheld' : 'released'} successfully.`, 'success');
      setWithholdTarget(null);
      setWithholdReason('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Withhold operation failed.', 'danger');
    }
  };

  // 6. Open Amendment Modal
  const openAmendmentModal = async (mark: any) => {
    setSelectedMarkForAmend(mark);
    setAmendMarks(mark.marks_obtained);
    setAmendAbsent(mark.is_absent);
    setAmendReason('');
    try {
      const history = await api.getMarkAmendments(mark.id);
      setAmendmentHistory(history);
    } catch {
      setAmendmentHistory([]);
    }
  };

  // 7. Submit Amendment
  const handleSubmitAmendment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMarkForAmend) return;
    if (!amendReason.trim()) {
      alert('A formal justification reason is strictly required for mark amendments.');
      return;
    }

    try {
      await api.amendOfficialMark(selectedMarkForAmend.id, {
        new_marks_obtained: amendMarks,
        new_is_absent: amendAbsent,
        reason: amendReason,
      });
      showMessage('Official mark amended successfully. Calculated results automatically synchronized!', 'success');
      setSelectedMarkForAmend(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Mark amendment failed.', 'danger');
    }
  };

  // 8. Batch Review & Approval Handlers
  const handleInspectBatchRows = async (batch: any) => {
    setSelectedBatchForReview(batch);
    setLoadingBatchRows(true);
    try {
      const rows = await api.getBatchRows(batch.id);
      setBatchReviewRows(rows);
    } catch (err: any) {
      showMessage(err.message || 'Failed to load batch rows', 'danger');
    } finally {
      setLoadingBatchRows(false);
    }
  };

  const handleApproveBatch = async (batchId: string) => {
    if (!confirm('Are you sure you want to approve this marks batch and transfer all rows to official academic marks?')) {
      return;
    }
    setLoading(true);
    try {
      await api.approveBatch(batchId);
      showMessage('Batch approved successfully and imported into official records!', 'success');
      setSelectedBatchForReview(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Batch approval failed', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmRejectBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectModalBatch || !rejectionReason.trim()) {
      alert('A mandatory rejection reason is required for administrative audit records.');
      return;
    }
    setLoading(true);
    try {
      await api.rejectBatch(rejectModalBatch.id, rejectionReason.trim());
      showMessage('Batch rejected and returned to faculty member with notes.', 'success');
      setRejectModalBatch(null);
      setRejectionReason('');
      setSelectedBatchForReview(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Rejection failed', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 9. Entity Creation Handlers
  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createSession({
        name: newSessionName,
        academic_year: newSessionYear,
        semester_number: newSessionSem,
      });
      showMessage(`Examination Session "${newSessionName}" created!`, 'success');
      setShowSessionModal(false);
      setNewSessionName('');
      loadSessions();
    } catch (err: any) {
      showMessage(err.message || 'Failed to create session', 'danger');
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCourse({
        code: newCourseCode.trim().toUpperCase(),
        name: newCourseName.trim(),
        credits: newCourseCredits,
        pass_percentage: newCoursePassPct,
      });
      showMessage(`Course "${newCourseCode}" registered successfully!`, 'success');
      setShowCourseModal(false);
      setNewCourseCode('');
      setNewCourseName('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to create course', 'danger');
    }
  };

  const handleCreateTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teacherDeptId) {
      showMessage('Please select a department for the faculty member', 'danger');
      return;
    }
    setLoading(true);
    try {
      await api.createTeacher({
        email: teacherEmail.trim(),
        password: teacherPassword,
        full_name: teacherName.trim(),
        employee_id: teacherEmpId.trim(),
        department_id: teacherDeptId,
        designation: teacherDesignation.trim(),
      });
      showMessage(`Faculty member "${teacherName}" registered successfully!`, 'success');
      setShowTeacherModal(false);
      setTeacherName('');
      setTeacherEmail('');
      setTeacherPassword('');
      setTeacherEmpId('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to register faculty member', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentProgId) {
      showMessage('Please select an academic program for the student', 'danger');
      return;
    }
    setLoading(true);
    try {
      await api.createStudent({
        email: studentEmail.trim(),
        password: studentPassword,
        full_name: studentName.trim(),
        registration_number: studentRegNo.trim(),
        roll_number: studentRollNo.trim() || undefined,
        program_id: studentProgId,
        current_semester: studentSem,
      });
      showMessage(`Student "${studentName}" (${studentRegNo}) registered successfully!`, 'success');
      setShowStudentModal(false);
      setStudentName('');
      setStudentEmail('');
      setStudentPassword('');
      setStudentRegNo('');
      setStudentRollNo('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to register student', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    const sessId = assignSessionId || selectedSessionId;
    if (!assignTeacherId || !assignCourseId || !sessId) {
      showMessage('Please select teacher, course, and session', 'danger');
      return;
    }
    setLoading(true);
    try {
      await api.createAssignment({
        teacher_id: assignTeacherId,
        course_id: assignCourseId,
        session_id: sessId,
      });
      showMessage('Faculty assigned to course successfully!', 'success');
      setShowAssignModal(false);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to assign faculty member', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    const sessId = enrollSessionId || selectedSessionId;
    if (!enrollStudentId || !enrollCourseId || !sessId) {
      showMessage('Please select student, course, and session', 'danger');
      return;
    }
    setLoading(true);
    try {
      await api.createEnrollment({
        student_id: enrollStudentId,
        course_id: enrollCourseId,
        session_id: sessId,
      });
      showMessage('Student enrolled in course successfully!', 'success');
      setShowEnrollModal(false);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to enroll student', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createDepartment({
        code: newDeptCode.trim().toUpperCase(),
        name: newDeptName.trim(),
      });
      showMessage(`Department "${newDeptCode}" created successfully!`, 'success');
      setShowDeptModal(false);
      setNewDeptCode('');
      setNewDeptName('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to create department', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProgDeptId) {
      showMessage('Please select a department for the program', 'danger');
      return;
    }
    setLoading(true);
    try {
      await api.createProgram({
        department_id: newProgDeptId,
        code: newProgCode.trim().toUpperCase(),
        name: newProgName.trim(),
        total_semesters: newProgSemesters,
      });
      showMessage(`Academic Program "${newProgCode}" created successfully!`, 'success');
      setShowProgModal(false);
      setNewProgCode('');
      setNewProgName('');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to create academic program', 'danger');
    } finally {
      setLoading(false);
    }
  };

  // 10. Direct Entity Edit & Deletion Handlers
  const openEditTeacher = (t: any) => {
    setEditingTeacher(t);
    setEditTeacherName(t.full_name || '');
    setEditTeacherEmail(t.email || '');
    setEditTeacherEmpId(t.employee_id || '');
    setEditTeacherDeptId(t.department_id || '');
    setEditTeacherDesignation(t.designation || 'Assistant Professor');
    setEditTeacherActive(t.is_active !== false);
    setEditTeacherPassword('');
  };

  const handleUpdateTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTeacher) return;
    setLoading(true);
    try {
      await api.updateTeacher(editingTeacher.id, {
        full_name: editTeacherName.trim(),
        email: editTeacherEmail.trim().toLowerCase(),
        employee_id: editTeacherEmpId.trim().toUpperCase(),
        department_id: editTeacherDeptId,
        designation: editTeacherDesignation.trim(),
        is_active: editTeacherActive,
        ...(editTeacherPassword ? { password: editTeacherPassword } : {}),
      });
      showMessage(`Faculty member "${editTeacherName}" updated successfully!`, 'success');
      setEditingTeacher(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update faculty member', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTeacher = async (t: any) => {
    if (!confirm(`Are you sure you want to delete faculty member "${t.full_name}" (${t.employee_id})? This will also remove login credentials and course assignments.`)) return;
    setLoading(true);
    try {
      await api.deleteTeacher(t.id);
      showMessage(`Faculty member "${t.full_name}" deleted successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to delete faculty member', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const openEditStudent = (s: any) => {
    setEditingStudent(s);
    setEditStudentName(s.full_name || '');
    setEditStudentEmail(s.email || '');
    setEditStudentRegNo(s.registration_number || '');
    setEditStudentRollNo(s.roll_number || '');
    setEditStudentProgId(s.program_id || '');
    setEditStudentSem(s.current_semester || 1);
    setEditStudentActive(s.is_active !== false);
    setEditStudentPassword('');
  };

  const handleUpdateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStudent) return;
    setLoading(true);
    try {
      await api.updateStudent(editingStudent.id, {
        full_name: editStudentName.trim(),
        email: editStudentEmail.trim().toLowerCase(),
        registration_number: editStudentRegNo.trim().toUpperCase(),
        roll_number: editStudentRollNo.trim() || undefined,
        program_id: editStudentProgId,
        current_semester: editStudentSem,
        is_active: editStudentActive,
        ...(editStudentPassword ? { password: editStudentPassword } : {}),
      });
      showMessage(`Student "${editStudentName}" updated successfully!`, 'success');
      setEditingStudent(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update student', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteStudent = async (s: any) => {
    if (!confirm(`Are you sure you want to delete student "${s.full_name}" (${s.registration_number})? This will also remove course enrollments and user credentials.`)) return;
    setLoading(true);
    try {
      await api.deleteStudent(s.id);
      showMessage(`Student "${s.full_name}" deleted successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to delete student', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAssignment = async (a: any) => {
    if (!confirm(`Are you sure you want to revoke assignment of ${a.teacher_name} for course ${a.course_code}?`)) return;
    setLoading(true);
    try {
      await api.deleteAssignment(a.id);
      showMessage(`Course allocation revoked successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to revoke course allocation', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEnrollment = async (e: any) => {
    if (!confirm(`Are you sure you want to remove enrollment for student ${e.student_name} from ${e.course_code}?`)) return;
    setLoading(true);
    try {
      await api.deleteEnrollment(e.id);
      showMessage(`Course enrollment removed successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to remove course enrollment', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const openEditDept = (d: any) => {
    setEditingDept(d);
    setEditDeptCode(d.code || '');
    setEditDeptName(d.name || '');
    setEditDeptActive(d.is_active !== false);
  };

  const handleUpdateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDept) return;
    setLoading(true);
    try {
      await api.updateDepartment(editingDept.id, {
        code: editDeptCode.trim().toUpperCase(),
        name: editDeptName.trim(),
        is_active: editDeptActive,
      });
      showMessage(`Department updated successfully!`, 'success');
      setEditingDept(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update department', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDepartment = async (d: any) => {
    if (!confirm(`Are you sure you want to delete department "${d.name}" (${d.code})?`)) return;
    setLoading(true);
    try {
      await api.deleteDepartment(d.id);
      showMessage(`Department deleted successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to delete department', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const openEditProg = (p: any) => {
    setEditingProg(p);
    setEditProgDeptId(p.department_id || '');
    setEditProgCode(p.code || '');
    setEditProgName(p.name || '');
    setEditProgSemesters(p.total_semesters || 8);
    setEditProgActive(p.is_active !== false);
  };

  const handleUpdateProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProg) return;
    setLoading(true);
    try {
      await api.updateProgram(editingProg.id, {
        department_id: editProgDeptId,
        code: editProgCode.trim().toUpperCase(),
        name: editProgName.trim(),
        total_semesters: editProgSemesters,
        is_active: editProgActive,
      });
      showMessage(`Degree program updated successfully!`, 'success');
      setEditingProg(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update program', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProgram = async (p: any) => {
    if (!confirm(`Are you sure you want to delete program "${p.name}" (${p.code})?`)) return;
    setLoading(true);
    try {
      await api.deleteProgram(p.id);
      showMessage(`Degree program deleted successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to delete program', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const openEditCourse = (c: any) => {
    setEditingCourse(c);
    setEditCourseCode(c.code || '');
    setEditCourseName(c.name || '');
    setEditCourseCredits(c.credits ?? 3.0);
    setEditCoursePassPct(c.pass_percentage ?? 40.0);
    setEditCourseActive(c.is_active !== false);
  };

  const handleUpdateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCourse) return;
    setLoading(true);
    try {
      await api.updateCourse(editingCourse.id, {
        code: editCourseCode.trim().toUpperCase(),
        name: editCourseName.trim(),
        credits: editCourseCredits,
        pass_percentage: editCoursePassPct,
        is_active: editCourseActive,
      });
      showMessage(`Course updated successfully!`, 'success');
      setEditingCourse(null);
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to update course', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCourse = async (c: any) => {
    if (!confirm(`Are you sure you want to delete course "${c.name}" (${c.code})?`)) return;
    setLoading(true);
    try {
      await api.deleteCourse(c.id);
      showMessage(`Course deleted successfully!`, 'success');
      loadSessionData(selectedSessionId);
    } catch (err: any) {
      showMessage(err.message || 'Failed to delete course', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const openEditSession = (s: any) => {
    setEditingSession(s);
    setEditSessionName(s.name || '');
    setEditSessionYear(s.academic_year || '');
    setEditSessionSem(s.semester_number || 1);
    setEditSessionStatus(s.status || 'DRAFT');
  };

  const handleUpdateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSession) return;
    setLoading(true);
    try {
      await api.updateSession(editingSession.id, {
        name: editSessionName.trim(),
        academic_year: editSessionYear.trim(),
        semester_number: editSessionSem,
        status: editSessionStatus,
      });
      showMessage(`Examination session updated successfully!`, 'success');
      setEditingSession(null);
      loadSessions();
    } catch (err: any) {
      showMessage(err.message || 'Failed to update session', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (s: any) => {
    if (!confirm(`Are you sure you want to delete examination session "${s.name}"? This will remove all associated session records.`)) return;
    setLoading(true);
    try {
      await api.deleteSession(s.id);
      showMessage(`Examination session deleted successfully!`, 'success');
      setSelectedSessionId('');
      loadSessions();
    } catch (err: any) {
      showMessage(err.message || 'Failed to delete session', 'danger');
    } finally {
      setLoading(false);
    }
  };

  const currentSessionObj = sessions.find((s) => s.id === selectedSessionId);

  return (
    <div>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>University Administration Control Deck</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Supervise evaluation sessions, review submitted marks batches, execute the calculation engine, and manage official result publications.
          </p>
        </div>

        {/* Global Session Selector */}
        <div style={{ minWidth: '280px' }}>
          <label className="form-label">Active Examination Session</label>
          <select
            className="form-select"
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.academic_year}) &bull; [{s.status}]
              </option>
            ))}
          </select>
        </div>
      </div>

      {actionMsg && (
        <div style={{
          padding: '1rem',
          background: actionMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
          border: `1px solid ${actionMsg.type === 'success' ? 'var(--success-border)' : 'var(--danger-border)'}`,
          borderRadius: 'var(--radius-md)',
          color: actionMsg.type === 'success' ? 'var(--success)' : 'var(--danger)',
          marginBottom: '1.5rem',
        }}>
          {actionMsg.type === 'success' ? '✅' : '⚠️'} {actionMsg.text}
        </div>
      )}

      {/* Tabs */}
      <div className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'calculate_publish' ? 'active' : ''}`}
          onClick={() => setActiveTab('calculate_publish')}
        >
          ⚡ Calculation & Publication
        </button>
        <button
          className={`tab-btn ${activeTab === 'directory' ? 'active' : ''}`}
          onClick={() => setActiveTab('directory')}
        >
          👥 Faculty, Students & Directory
        </button>
        <button
          className={`tab-btn ${activeTab === 'imports' ? 'active' : ''}`}
          onClick={() => setActiveTab('imports')}
        >
          📥 Marks Batches & Review
        </button>
        <button
          className={`tab-btn ${activeTab === 'amendments' ? 'active' : ''}`}
          onClick={() => setActiveTab('amendments')}
        >
          📝 Official Marks & Amendments
        </button>
        <button
          className={`tab-btn ${activeTab === 'sessions' ? 'active' : ''}`}
          onClick={() => setActiveTab('sessions')}
        >
          🏛️ Session Lifecycle
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          🔒 Compliance Audit Trail
        </button>
        <button
          className={`tab-btn ${activeTab === 'database' ? 'active' : ''}`}
          onClick={() => setActiveTab('database')}
        >
          🗄️ Database Studio
        </button>
      </div>

      {/* TAB 1: CALCULATION & PUBLICATION */}
      {activeTab === 'calculate_publish' && (
        <div>
          {/* Action Header Card */}
          <div className="glass-panel" style={{ marginBottom: '1.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                CURRENT SESSION STATUS
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem' }}>
                <span className="badge badge-info" style={{ fontSize: '1rem', padding: '0.4rem 1rem' }}>
                  {currentSessionObj?.status || 'UNKNOWN'}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  Term: {currentSessionObj?.academic_year} &bull; Semester {currentSessionObj?.semester_number}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary"
                onClick={() => handleCalculate(false)}
                disabled={loading || currentSessionObj?.status === 'PUBLISHED'}
              >
                ⚙️ Run Calculation Engine
              </button>

              {currentSessionObj?.status === 'CALCULATED' && (
                <button
                  className="btn btn-success"
                  onClick={handlePublish}
                  disabled={loading}
                >
                  🚀 Publish Official Results
                </button>
              )}

              {currentSessionObj?.status === 'PUBLISHED' && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={handleUnpublish}
                  disabled={loading}
                >
                  ↩️ Rollback (Unpublish)
                </button>
              )}
            </div>
          </div>

          {/* Metrics Overview */}
          {summary && (
            <div className="metrics-grid">
              <div className="stat-card">
                <div className="stat-label">Students Evaluated</div>
                <div className="stat-value">{summary.total_students_evaluated}</div>
                <div className="stat-subtext">Out of {summary.total_students_enrolled} enrolled</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Overall Pass Rate</div>
                <div className="stat-value" style={{ color: 'var(--success)' }}>
                  {summary.overall_pass_percentage.toFixed(1)}%
                </div>
                <div className="stat-subtext">{summary.total_passed} Passed &bull; {summary.total_failed} Failed</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Top Performance</div>
                <div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>
                  {summary.highest_percentage.toFixed(1)}%
                </div>
                <div className="stat-subtext">Class Average: {summary.average_percentage.toFixed(1)}%</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Withheld Records</div>
                <div className="stat-value" style={{ color: summary.total_withheld > 0 ? 'var(--warning)' : '#fff' }}>
                  {summary.total_withheld}
                </div>
                <div className="stat-subtext">Masked from student portal</div>
              </div>
            </div>
          )}

          {/* Student Results List */}
          <div className="glass-panel">
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>🎓 Evaluated Student Results Roster</h3>
            {sessionResults.length === 0 ? (
              <p style={{ color: 'var(--text-dim)' }}>No calculated results found. Click "Run Calculation Engine" above.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Reg Number</th>
                      <th>Student Name</th>
                      <th>Program</th>
                      <th>Total Obtained</th>
                      <th>Max Marks</th>
                      <th>Percentage</th>
                      <th>Result Status</th>
                      <th>Withheld?</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessionResults.map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{r.registration_number}</td>
                        <td style={{ fontWeight: 500 }}>{r.student_name}</td>
                        <td>{r.program_code}</td>
                        <td style={{ fontWeight: 700 }}>{r.total_marks_obtained}</td>
                        <td>{r.total_max_marks}</td>
                        <td>{r.percentage.toFixed(2)}%</td>
                        <td>
                          <span className={`badge ${r.result_status === 'PASS' ? 'badge-pass' : 'badge-fail'}`}>
                            {r.result_status}
                          </span>
                        </td>
                        <td>
                          {r.is_withheld ? (
                            <span className="badge badge-warning" title={r.withheld_reason || ''}>
                              WITHHELD
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>RELEASED</span>
                          )}
                        </td>
                        <td>
                          <button
                            className={`btn btn-sm ${r.is_withheld ? 'btn-success' : 'btn-danger'}`}
                            onClick={() => {
                              setWithholdTarget(r);
                              setWithholdReason(r.withheld_reason || '');
                            }}
                          >
                            {r.is_withheld ? 'Release' : 'Withhold'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: MARKS BATCHES & REVIEW */}
      {activeTab === 'imports' && (
        <div>
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>📥 Submitted Marks Import Batches</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
              Faculty-submitted CSV marks batches. Batches in <strong>PENDING_APPROVAL</strong> require formal administrative verification and transactional import.
            </p>

            {batches.length === 0 ? (
              <p style={{ color: 'var(--text-dim)' }}>No mark batches submitted for this session yet.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>File Name</th>
                      <th>Total Rows</th>
                      <th>Valid</th>
                      <th>Errors</th>
                      <th>Max Marks</th>
                      <th>Status</th>
                      <th>Submitted At</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.map((b) => (
                      <tr key={b.id}>
                        <td style={{ fontWeight: 500 }}>{b.file_name}</td>
                        <td>{b.total_rows}</td>
                        <td style={{ color: 'var(--success)' }}>{b.valid_rows}</td>
                        <td style={{ color: b.error_rows > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>{b.error_rows}</td>
                        <td>{b.max_marks}</td>
                        <td>
                          <span className={`badge ${b.status === 'IMPORTED' ? 'badge-pass' : b.status === 'PENDING_APPROVAL' ? 'badge-accent' : 'badge-fail'}`}>
                            {b.status}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                          {new Date(b.created_at).toLocaleDateString()}
                        </td>
                        <td style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleInspectBatchRows(b)}
                          >
                            Inspect
                          </button>
                          {b.status === 'PENDING_APPROVAL' && (
                            <>
                              <button
                                className="btn btn-success btn-sm"
                                onClick={() => handleApproveBatch(b.id)}
                                disabled={loading}
                              >
                                Approve
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                onClick={() => setRejectModalBatch(b)}
                                disabled={loading}
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Staged Rows Inspection */}
          {selectedBatchForReview && (
            <div className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h4 style={{ fontSize: '1.15rem' }}>
                    Staged Rows: {selectedBatchForReview.file_name} ({selectedBatchForReview.status})
                  </h4>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Total: {selectedBatchForReview.total_rows} | Valid: {selectedBatchForReview.valid_rows} | Errors: {selectedBatchForReview.error_rows}
                  </p>
                </div>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setSelectedBatchForReview(null)}
                >
                  Close Inspection
                </button>
              </div>

              {loadingBatchRows ? (
                <p style={{ color: 'var(--text-muted)' }}>Loading staged batch rows...</p>
              ) : batchReviewRows.length === 0 ? (
                <p style={{ color: 'var(--text-dim)' }}>No staged rows found.</p>
              ) : (
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Row</th>
                        <th>Student Registration #</th>
                        <th>Raw Marks</th>
                        <th>Absent?</th>
                        <th>Validation Status</th>
                        <th>Error Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batchReviewRows.map((r: any) => (
                        <tr key={r.id || r.row_number}>
                          <td>{r.row_number}</td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{r.raw_registration_number}</td>
                          <td>{r.is_absent ? <span style={{ color: 'var(--warning)' }}>AB</span> : r.raw_marks_obtained}</td>
                          <td>{r.is_absent ? 'YES' : 'NO'}</td>
                          <td>
                            <span className={`badge ${r.is_valid ? 'badge-pass' : 'badge-fail'}`}>
                              {r.is_valid ? 'VALID' : 'INVALID'}
                            </span>
                          </td>
                          <td style={{ color: r.is_valid ? 'var(--text-muted)' : 'var(--danger)', fontSize: '0.85rem' }}>
                            {r.is_valid
                              ? 'OK'
                              : Array.isArray(r.validation_errors)
                                ? r.validation_errors.map((e: any) => e.message).join('; ')
                                : 'Error'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: OFFICIAL MARKS & AMENDMENTS */}
      {activeTab === 'amendments' && (
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem' }}>Official Marks Ledger & Senate Amendment Log</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Audited student marks officially committed from approved batches. Amendments require formal senate justification.
              </p>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reg Number</th>
                  <th>Student Name</th>
                  <th>Course</th>
                  <th>Marks</th>
                  <th>Max Marks</th>
                  <th>Percentage</th>
                  <th>Absent?</th>
                  <th>Amendment Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {officialMarks.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{m.registration_number}</td>
                    <td>{m.student_name}</td>
                    <td><strong style={{ color: 'var(--accent-cyan)' }}>{m.course_code}</strong> - {m.course_name}</td>
                    <td style={{ fontWeight: 700 }}>{m.is_absent ? 'AB' : m.marks_obtained}</td>
                    <td>{m.max_marks}</td>
                    <td>{m.percentage.toFixed(2)}%</td>
                    <td>{m.is_absent ? 'YES' : 'NO'}</td>
                    <td>
                      {m.is_amended ? (
                        <span className="badge badge-warning">AMENDED</span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>ORIGINAL</span>
                      )}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => openAmendmentModal(m)}
                      >
                        ✏️ Amend Mark
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: SESSION LIFECYCLE & INSTITUTIONAL SETUP */}
      {activeTab === 'sessions' && (
        <div>
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem' }}>Academic Session Workflow State Machine</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  Regulate the active phase of this examination session. Transitions enforce academic integrity constraints.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-primary btn-sm" onClick={() => setShowSessionModal(true)}>
                  ➕ New Examination Session
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => setShowCourseModal(true)}>
                  ➕ Register New Course
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary"
                onClick={() => handleStatusChange('MARKS_ENTRY_OPEN')}
                disabled={currentSessionObj?.status === 'MARKS_ENTRY_OPEN'}
              >
                🔓 Open Marks Entry
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => handleStatusChange('MARKS_LOCKED')}
                disabled={currentSessionObj?.status === 'MARKS_LOCKED'}
              >
                🔒 Lock Marks Entry
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => handleStatusChange('ARCHIVED')}
                disabled={currentSessionObj?.status === 'ARCHIVED'}
              >
                📦 Archive Session
              </button>
            </div>
          </div>

          {/* All Examination Sessions Table */}
          <div className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem' }}>All Examination Sessions ({sessions.length})</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  Manage, modify details, or remove examination sessions across terms.
                </p>
              </div>
            </div>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Session Name</th>
                    <th>Academic Year</th>
                    <th>Semester</th>
                    <th>Lifecycle Status</th>
                    <th style={{ width: '140px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s) => (
                    <tr key={s.id}>
                      <td style={{ fontWeight: 600 }}>{s.name}</td>
                      <td><code>{s.academic_year}</code></td>
                      <td>Semester {s.semester_number}</td>
                      <td>
                        <span className="badge badge-info">{s.status}</span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.35rem' }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                            onClick={() => openEditSession(s)}
                            title="Edit Session Details"
                          >
                            ✏️ Edit
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                            onClick={() => handleDeleteSession(s)}
                            title="Delete Session"
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="glass-panel">
          <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>🔒 Immutable Compliance Audit Log</h3>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>User</th>
                  <th>Entity Type</th>
                  <th>Entity ID</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td><span className="badge badge-info">{log.action}</span></td>
                    <td style={{ fontWeight: 600 }}>{log.user_name}</td>
                    <td style={{ color: 'var(--accent-cyan)' }}>{log.entity_type}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{log.entity_id ? log.entity_id.substring(0, 8) + '...' : '—'}</td>
                    <td style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {log.details ? JSON.stringify(log.details) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: FACULTY, STUDENTS & ACADEMIC DIRECTORY */}
      {activeTab === 'directory' && (
        <div>
          {/* Sub Navigation */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            <button
              className={`btn btn-sm ${directorySubTab === 'teachers' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setDirectorySubTab('teachers')}
            >
              👨‍🏫 Faculty Members ({teachers.length})
            </button>
            <button
              className={`btn btn-sm ${directorySubTab === 'students' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setDirectorySubTab('students')}
            >
              🎓 Students ({students.length})
            </button>
            <button
              className={`btn btn-sm ${directorySubTab === 'assignments' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setDirectorySubTab('assignments')}
            >
              📋 Course Allocations ({assignments.length})
            </button>
            <button
              className={`btn btn-sm ${directorySubTab === 'enrollments' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setDirectorySubTab('enrollments')}
            >
              📝 Student Enrollments ({enrollments.length})
            </button>
            <button
              className={`btn btn-sm ${directorySubTab === 'academic_units' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setDirectorySubTab('academic_units')}
            >
              🏛️ Departments & Programs ({departments.length})
            </button>
          </div>

          {/* SubTab 1: TEACHERS */}
          {directorySubTab === 'teachers' && (
            <div className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem' }}>Faculty & Teaching Staff</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Registered faculty members authorized to upload and submit examination marks.
                  </p>
                </div>
                <button className="btn btn-primary btn-sm" onClick={() => setShowTeacherModal(true)}>
                  ➕ Register Faculty Member
                </button>
              </div>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Full Name</th>
                      <th>Email</th>
                      <th>Employee ID</th>
                      <th>Designation</th>
                      <th>Department</th>
                      <th>Status</th>
                      <th style={{ width: '140px' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {teachers.map((t) => {
                      const dept = departments.find((d) => d.id === t.department_id);
                      return (
                        <tr key={t.id}>
                          <td style={{ fontWeight: 600 }}>{t.full_name}</td>
                          <td style={{ color: 'var(--accent-cyan)' }}>{t.email}</td>
                          <td><code>{t.employee_id}</code></td>
                          <td>{t.designation}</td>
                          <td>{dept ? `${dept.code} - ${dept.name}` : t.department_id}</td>
                          <td>
                            <span className={`badge ${t.is_active ? 'badge-success' : 'badge-danger'}`}>
                              {t.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.35rem' }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => openEditTeacher(t)}
                                title="Edit Faculty Member"
                              >
                                ✏️ Edit
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => handleDeleteTeacher(t)}
                                title="Delete Faculty Member"
                              >
                                🗑️ Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {teachers.length === 0 && (
                      <tr>
                        <td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                          No faculty members registered yet. Click "Register Faculty Member" to add one.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SubTab 2: STUDENTS */}
          {directorySubTab === 'students' && (
            <div className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem' }}>Enrolled Students Directory</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Active students eligible for course enrollment and electronic marksheet generation.
                  </p>
                </div>
                <button className="btn btn-primary btn-sm" onClick={() => setShowStudentModal(true)}>
                  ➕ Register New Student
                </button>
              </div>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Registration #</th>
                      <th>Student Name</th>
                      <th>Official Email</th>
                      <th>Roll #</th>
                      <th>Program</th>
                      <th>Semester</th>
                      <th>Status</th>
                      <th style={{ width: '140px' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((s) => {
                      const prog = programs.find((p) => p.id === s.program_id);
                      return (
                        <tr key={s.id}>
                          <td><code>{s.registration_number}</code></td>
                          <td style={{ fontWeight: 600 }}>{s.full_name}</td>
                          <td style={{ color: 'var(--accent-cyan)' }}>{s.email}</td>
                          <td>{s.roll_number || '—'}</td>
                          <td>{prog ? prog.code : s.program_id}</td>
                          <td>Sem {s.current_semester}</td>
                          <td>
                            <span className={`badge ${s.is_active ? 'badge-success' : 'badge-danger'}`}>
                              {s.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.35rem' }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => openEditStudent(s)}
                                title="Edit Student"
                              >
                                ✏️ Edit
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => handleDeleteStudent(s)}
                                title="Delete Student"
                              >
                                🗑️ Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {students.length === 0 && (
                      <tr>
                        <td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                          No students registered yet. Click "Register New Student" to add students.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SubTab 3: ASSIGNMENTS */}
          {directorySubTab === 'assignments' && (
            <div className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem' }}>Faculty Course Allocations</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Courses allocated to teachers for marks evaluation in examination sessions.
                  </p>
                </div>
                <button className="btn btn-primary btn-sm" onClick={() => setShowAssignModal(true)}>
                  ➕ Assign Faculty to Course
                </button>
              </div>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Faculty Member</th>
                      <th>Employee ID</th>
                      <th>Course</th>
                      <th>Examination Session</th>
                      <th>Status</th>
                      <th style={{ width: '100px' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((a) => (
                      <tr key={a.id}>
                        <td style={{ fontWeight: 600 }}>{a.teacher_name}</td>
                        <td><code>{a.employee_id}</code></td>
                        <td><strong>{a.course_code}</strong> - {a.course_name}</td>
                        <td>{a.session_name || selectedSessionId}</td>
                        <td>
                          <span className={`badge ${a.is_active ? 'badge-success' : 'badge-danger'}`}>
                            {a.is_active ? 'Active' : 'Revoked'}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-danger btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                            onClick={() => handleDeleteAssignment(a)}
                            title="Revoke Course Allocation"
                          >
                            🗑️ Revoke
                          </button>
                        </td>
                      </tr>
                    ))}
                    {assignments.length === 0 && (
                      <tr>
                        <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                          No faculty course allocations found for this session. Click "Assign Faculty to Course" to create one.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SubTab 4: ENROLLMENTS */}
          {directorySubTab === 'enrollments' && (
            <div className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem' }}>Student Course Enrollments</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Registered course examinees for this active examination session.
                  </p>
                </div>
                <button className="btn btn-primary btn-sm" onClick={() => setShowEnrollModal(true)}>
                  ➕ Enroll Student in Course
                </button>
              </div>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Registration #</th>
                      <th>Student Name</th>
                      <th>Course</th>
                      <th>Session</th>
                      <th>Status</th>
                      <th style={{ width: '100px' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enrollments.map((e) => (
                      <tr key={e.id}>
                        <td><code>{e.registration_number}</code></td>
                        <td style={{ fontWeight: 600 }}>{e.student_name}</td>
                        <td><strong>{e.course_code}</strong> - {e.course_name}</td>
                        <td>{currentSessionObj?.name || 'Current Session'}</td>
                        <td>
                          <span className={`badge ${e.is_active ? 'badge-success' : 'badge-danger'}`}>
                            {e.is_active ? 'Enrolled' : 'Dropped'}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-danger btn-sm"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                            onClick={() => handleDeleteEnrollment(e)}
                            title="Remove Enrollment"
                          >
                            🗑️ Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                    {enrollments.length === 0 && (
                      <tr>
                        <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                          No course enrollments found for this session. Click "Enroll Student in Course" to enroll students.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SubTab 5: ACADEMIC UNITS */}
          {directorySubTab === 'academic_units' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
                <div className="glass-panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1.15rem' }}>Academic Departments ({departments.length})</h3>
                    <button className="btn btn-primary btn-sm" onClick={() => setShowDeptModal(true)}>
                      ➕ Add Department
                    </button>
                  </div>
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Code</th>
                          <th>Department Name</th>
                          <th>Status</th>
                          <th style={{ width: '110px' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {departments.map((d) => (
                          <tr key={d.id}>
                            <td><code>{d.code}</code></td>
                            <td>{d.name}</td>
                            <td>
                              <span className={`badge ${d.is_active !== false ? 'badge-success' : 'badge-danger'}`}>
                                {d.is_active !== false ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td>
                              <div style={{ display: 'flex', gap: '0.35rem' }}>
                                <button
                                  className="btn btn-secondary btn-sm"
                                  style={{ padding: '0.2rem 0.45rem', fontSize: '0.75rem' }}
                                  onClick={() => openEditDept(d)}
                                  title="Edit Department"
                                >
                                  ✏️
                                </button>
                                <button
                                  className="btn btn-danger btn-sm"
                                  style={{ padding: '0.2rem 0.45rem', fontSize: '0.75rem' }}
                                  onClick={() => handleDeleteDepartment(d)}
                                  title="Delete Department"
                                >
                                  🗑️
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                        {departments.length === 0 && (
                          <tr>
                            <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1rem' }}>
                              No departments found.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="glass-panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ fontSize: '1.15rem' }}>Degree Programs ({programs.length})</h3>
                    <button className="btn btn-primary btn-sm" onClick={() => setShowProgModal(true)}>
                      ➕ Add Program
                    </button>
                  </div>
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Code</th>
                          <th>Program Name</th>
                          <th>Semesters</th>
                          <th style={{ width: '110px' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {programs.map((p) => (
                          <tr key={p.id}>
                            <td><code>{p.code}</code></td>
                            <td>{p.name}</td>
                            <td>{p.total_semesters} Sem</td>
                            <td>
                              <div style={{ display: 'flex', gap: '0.35rem' }}>
                                <button
                                  className="btn btn-secondary btn-sm"
                                  style={{ padding: '0.2rem 0.45rem', fontSize: '0.75rem' }}
                                  onClick={() => openEditProg(p)}
                                  title="Edit Program"
                                >
                                  ✏️
                                </button>
                                <button
                                  className="btn btn-danger btn-sm"
                                  style={{ padding: '0.2rem 0.45rem', fontSize: '0.75rem' }}
                                  onClick={() => handleDeleteProgram(p)}
                                  title="Delete Program"
                                >
                                  🗑️
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                        {programs.length === 0 && (
                          <tr>
                            <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1rem' }}>
                              No programs found.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Master Courses Catalog Panel */}
              <div className="glass-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.15rem' }}>Active Course Offerings ({courses.length})</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      Master course catalog defining credits and minimum pass percentages across academic departments.
                    </p>
                  </div>
                  <button className="btn btn-primary btn-sm" onClick={() => setShowCourseModal(true)}>
                    ➕ Register New Course
                  </button>
                </div>
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Course Code</th>
                        <th>Course Name</th>
                        <th>Credits</th>
                        <th>Pass Mark %</th>
                        <th>Status</th>
                        <th style={{ width: '140px' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {courses.map((c) => (
                        <tr key={c.id}>
                          <td><code>{c.code}</code></td>
                          <td style={{ fontWeight: 600 }}>{c.name}</td>
                          <td>{c.credits} Credits</td>
                          <td>{c.pass_percentage}%</td>
                          <td>
                            <span className={`badge ${c.is_active !== false ? 'badge-success' : 'badge-danger'}`}>
                              {c.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '0.35rem' }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => openEditCourse(c)}
                                title="Edit Course"
                              >
                                ✏️ Edit
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                onClick={() => handleDeleteCourse(c)}
                                title="Delete Course"
                              >
                                🗑️ Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      {courses.length === 0 && (
                        <tr>
                          <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                            No courses in master catalog. Click "Register New Course" to add one.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB: DATABASE STUDIO */}
      {activeTab === 'database' && (
        <DatabaseStudio onNotify={showMessage} />
      )}

      {/* MODAL: REJECT BATCH */}
      {rejectModalBatch && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>❌ Reject Marks Batch: {rejectModalBatch.file_name}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setRejectModalBatch(null)}>✕</button>
            </div>
            <form onSubmit={handleConfirmRejectBatch}>
              <div className="modal-body">
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem', fontSize: '0.9rem' }}>
                  Please provide the exact reason for rejecting this marks submission. The faculty member will see this message and be instructed to correct their CSV.
                </p>
                <div className="form-group">
                  <label className="form-label">Rejection Justification</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="e.g. Mismatched maximum marks, missing 5 enrolled students."
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setRejectModalBatch(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger" disabled={loading}>
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE SESSION */}
      {showSessionModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>➕ Create Examination Session</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowSessionModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateSession}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Session Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    placeholder="e.g. Autumn 2026 Regular Examination"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Academic Year</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newSessionYear}
                    onChange={(e) => setNewSessionYear(e.target.value)}
                    placeholder="e.g. 2025-2026"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Semester Number</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    className="form-input"
                    value={newSessionSem}
                    onChange={(e) => setNewSessionSem(parseInt(e.target.value) || 1)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowSessionModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Session</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE COURSE */}
      {showCourseModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>➕ Register New Course</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowCourseModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateCourse}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Course Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newCourseCode}
                    onChange={(e) => setNewCourseCode(e.target.value)}
                    placeholder="e.g. CS301"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Course Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newCourseName}
                    onChange={(e) => setNewCourseName(e.target.value)}
                    placeholder="e.g. Database Management Systems"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Credits</label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="30"
                    className="form-input"
                    value={newCourseCredits}
                    onChange={(e) => setNewCourseCredits(parseFloat(e.target.value) || 3.0)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Pass Percentage</label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    max="100"
                    className="form-input"
                    value={newCoursePassPct}
                    onChange={(e) => setNewCoursePassPct(parseFloat(e.target.value) || 40.0)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCourseModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Register Course</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: POST-PUBLICATION AMENDMENT */}
      {selectedMarkForAmend && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Amend Official Mark: {selectedMarkForAmend.student_name}</h3>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedMarkForAmend(null)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmitAmendment}>
              <div className="modal-body">
                <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)' }}>
                  <div>Registration: <strong>{selectedMarkForAmend.registration_number}</strong></div>
                  <div>Course: <strong>{selectedMarkForAmend.course_code} - {selectedMarkForAmend.course_name}</strong></div>
                  <div>Current Official Mark: <strong>{selectedMarkForAmend.marks_obtained} / {selectedMarkForAmend.max_marks}</strong></div>
                </div>

                <div className="form-group">
                  <label className="form-label">New Marks Obtained (Max: {selectedMarkForAmend.max_marks})</label>
                  <input
                    type="number"
                    step="0.5"
                    className="form-input"
                    value={amendMarks}
                    disabled={amendAbsent}
                    onChange={(e) => setAmendMarks(parseFloat(e.target.value) || 0)}
                    required={!amendAbsent}
                  />
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={amendAbsent}
                      onChange={(e) => setAmendAbsent(e.target.checked)}
                    />
                    Mark Student as Absent (AB)
                  </label>
                </div>

                <div className="form-group">
                  <label className="form-label">Mandatory Correction Justification / Academic Senate Reason</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={amendReason}
                    onChange={(e) => setAmendReason(e.target.value)}
                    placeholder="e.g. Scrutiny committee re-evaluation, revised after verification."
                    required
                  />
                </div>

                {amendmentHistory.length > 0 && (
                  <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
                    <h5 style={{ marginBottom: '0.5rem' }}>Previous Amendments History</h5>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {amendmentHistory.map((h) => (
                        <div key={h.id} style={{ marginBottom: '0.5rem', padding: '0.5rem', background: 'var(--bg-surface-elevated)', borderRadius: '4px' }}>
                          Changed from <strong>{h.old_marks_obtained}</strong> to <strong>{h.new_marks_obtained}</strong> on {new Date(h.amended_at).toLocaleString()}: <em>"{h.reason}"</em>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedMarkForAmend(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirm & Sync Results
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: WITHHOLD CONFIRMATION */}
      {withholdTarget && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>{withholdTarget.is_withheld ? 'Release Result' : 'Withhold Result'}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setWithholdTarget(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ marginBottom: '1rem' }}>
                Are you sure you want to <strong>{withholdTarget.is_withheld ? 'release' : 'withhold'}</strong> the examination result for <strong>{withholdTarget.student_name}</strong> ({withholdTarget.registration_number})?
              </p>
              <div className="form-group">
                <label className="form-label">Reason / Administrative Notice</label>
                <input
                  type="text"
                  className="form-input"
                  value={withholdReason}
                  onChange={(e) => setWithholdReason(e.target.value)}
                  placeholder="e.g. Pending tuition clearance / Academic inquiry"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setWithholdTarget(null)}>Cancel</button>
              <button
                className={`btn ${withholdTarget.is_withheld ? 'btn-success' : 'btn-danger'}`}
                onClick={handleToggleWithhold}
              >
                Confirm {withholdTarget.is_withheld ? 'Release' : 'Withhold'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: REGISTER FACULTY MEMBER */}
      {showTeacherModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>👨‍🏫 Register Faculty Member</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowTeacherModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateTeacher}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Full Name & Title</label>
                  <input
                    type="text"
                    className="form-input"
                    value={teacherName}
                    onChange={(e) => setTeacherName(e.target.value)}
                    placeholder="e.g. Dr. Robert Noyce"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Official Academic Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={teacherEmail}
                    onChange={(e) => setTeacherEmail(e.target.value)}
                    placeholder="e.g. r.noyce@institution.edu"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Initial Password</label>
                  <input
                    type="password"
                    className="form-input"
                    value={teacherPassword}
                    onChange={(e) => setTeacherPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Employee ID / Faculty Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={teacherEmpId}
                    onChange={(e) => setTeacherEmpId(e.target.value)}
                    placeholder="e.g. FAC-104"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Department Affiliation</label>
                  <select
                    className="form-select"
                    value={teacherDeptId}
                    onChange={(e) => setTeacherDeptId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Academic Designation</label>
                  <input
                    type="text"
                    className="form-input"
                    value={teacherDesignation}
                    onChange={(e) => setTeacherDesignation(e.target.value)}
                    placeholder="e.g. Associate Professor"
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowTeacherModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Registering...' : 'Register Faculty Member'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: REGISTER STUDENT */}
      {showStudentModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>🎓 Register New Student</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowStudentModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateStudent}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Student Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    placeholder="e.g. Maya Lin"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Official Student Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={studentEmail}
                    onChange={(e) => setStudentEmail(e.target.value)}
                    placeholder="e.g. maya.lin@institution.edu"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Initial Password</label>
                  <input
                    type="password"
                    className="form-input"
                    value={studentPassword}
                    onChange={(e) => setStudentPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Registration / Matriculation Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={studentRegNo}
                    onChange={(e) => setStudentRegNo(e.target.value)}
                    placeholder="e.g. STU-2026-088"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Class Roll Number (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={studentRollNo}
                    onChange={(e) => setStudentRollNo(e.target.value)}
                    placeholder="e.g. 26-CS-088"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Enrolled Degree Program</label>
                  <select
                    className="form-select"
                    value={studentProgId}
                    onChange={(e) => setStudentProgId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Degree Program --</option>
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Current Semester Number</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    className="form-input"
                    value={studentSem}
                    onChange={(e) => setStudentSem(parseInt(e.target.value) || 1)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowStudentModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Registering...' : 'Register Student'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ASSIGN TEACHER TO COURSE */}
      {showAssignModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>📋 Allocate Course to Faculty</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowAssignModal(false)}>✕</button>
            </div>
            <form onSubmit={handleAssignTeacher}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Select Faculty Member</label>
                  <select
                    className="form-select"
                    value={assignTeacherId}
                    onChange={(e) => setAssignTeacherId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Faculty --</option>
                    {teachers.map((t) => (
                      <option key={t.id} value={t.id}>{t.full_name} ({t.employee_id})</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Select Course</label>
                  <select
                    className="form-select"
                    value={assignCourseId}
                    onChange={(e) => setAssignCourseId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Course --</option>
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Examination Session</label>
                  <select
                    className="form-select"
                    value={assignSessionId || selectedSessionId}
                    onChange={(e) => setAssignSessionId(e.target.value)}
                    required
                  >
                    {sessions.map((s) => (
                      <option key={s.id} value={s.id}>{s.name} ({s.academic_year})</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAssignModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Allocating...' : 'Allocate Course'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ENROLL STUDENT IN COURSE */}
      {showEnrollModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>📝 Enroll Student in Course</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowEnrollModal(false)}>✕</button>
            </div>
            <form onSubmit={handleEnrollStudent}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Select Student</label>
                  <select
                    className="form-select"
                    value={enrollStudentId}
                    onChange={(e) => setEnrollStudentId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Student --</option>
                    {students.map((s) => (
                      <option key={s.id} value={s.id}>{s.registration_number} - {s.full_name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Select Course</label>
                  <select
                    className="form-select"
                    value={enrollCourseId}
                    onChange={(e) => setEnrollCourseId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Course --</option>
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Examination Session</label>
                  <select
                    className="form-select"
                    value={enrollSessionId || selectedSessionId}
                    onChange={(e) => setEnrollSessionId(e.target.value)}
                    required
                  >
                    {sessions.map((s) => (
                      <option key={s.id} value={s.id}>{s.name} ({s.academic_year})</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEnrollModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Enrolling...' : 'Enroll Student'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD DEPARTMENT */}
      {showDeptModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>🏛️ Add Academic Department</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowDeptModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateDepartment}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Department Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newDeptCode}
                    onChange={(e) => setNewDeptCode(e.target.value)}
                    placeholder="e.g. MECH"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Department Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newDeptName}
                    onChange={(e) => setNewDeptName(e.target.value)}
                    placeholder="e.g. Department of Mechanical Engineering"
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowDeptModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Department'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD DEGREE PROGRAM */}
      {showProgModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>🎓 Add Degree Program</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowProgModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateProgram}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Parent Department</label>
                  <select
                    className="form-select"
                    value={newProgDeptId}
                    onChange={(e) => setNewProgDeptId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Program Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newProgCode}
                    onChange={(e) => setNewProgCode(e.target.value)}
                    placeholder="e.g. BTECH-MECH"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Program Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newProgName}
                    onChange={(e) => setNewProgName(e.target.value)}
                    placeholder="e.g. Bachelor of Technology in Mechanical Engineering"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Total Semesters</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    className="form-input"
                    value={newProgSemesters}
                    onChange={(e) => setNewProgSemesters(parseInt(e.target.value) || 8)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowProgModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Program'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT TEACHER */}
      {editingTeacher && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Edit Faculty Member: {editingTeacher.full_name}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingTeacher(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateTeacher}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editTeacherName}
                    onChange={(e) => setEditTeacherName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    className="form-input"
                    value={editTeacherEmail}
                    onChange={(e) => setEditTeacherEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Employee ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editTeacherEmpId}
                    onChange={(e) => setEditTeacherEmpId(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Department</label>
                  <select
                    className="form-select"
                    value={editTeacherDeptId}
                    onChange={(e) => setEditTeacherDeptId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Designation</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editTeacherDesignation}
                    onChange={(e) => setEditTeacherDesignation(e.target.value)}
                    placeholder="e.g. Associate Professor"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Reset Password (leave empty to keep unchanged)</label>
                  <input
                    type="password"
                    className="form-input"
                    value={editTeacherPassword}
                    onChange={(e) => setEditTeacherPassword(e.target.value)}
                    placeholder="Enter new password to reset"
                  />
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="editTeacherActive"
                    checked={editTeacherActive}
                    onChange={(e) => setEditTeacherActive(e.target.checked)}
                  />
                  <label htmlFor="editTeacherActive" style={{ cursor: 'pointer', margin: 0 }}>
                    Active (Authorized to login & manage marks)
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingTeacher(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT STUDENT */}
      {editingStudent && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Edit Student: {editingStudent.full_name}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingStudent(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateStudent}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editStudentName}
                    onChange={(e) => setEditStudentName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    className="form-input"
                    value={editStudentEmail}
                    onChange={(e) => setEditStudentEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Registration Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editStudentRegNo}
                    onChange={(e) => setEditStudentRegNo(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Roll Number (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editStudentRollNo}
                    onChange={(e) => setEditStudentRollNo(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Academic Program</label>
                  <select
                    className="form-select"
                    value={editStudentProgId}
                    onChange={(e) => setEditStudentProgId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Degree Program --</option>
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Current Semester</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    className="form-input"
                    value={editStudentSem}
                    onChange={(e) => setEditStudentSem(parseInt(e.target.value) || 1)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Reset Password (leave empty to keep unchanged)</label>
                  <input
                    type="password"
                    className="form-input"
                    value={editStudentPassword}
                    onChange={(e) => setEditStudentPassword(e.target.value)}
                    placeholder="Enter new password to reset"
                  />
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="editStudentActive"
                    checked={editStudentActive}
                    onChange={(e) => setEditStudentActive(e.target.checked)}
                  />
                  <label htmlFor="editStudentActive" style={{ cursor: 'pointer', margin: 0 }}>
                    Active (Enrolled student)
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingStudent(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT DEPARTMENT */}
      {editingDept && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Edit Department: {editingDept.code}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingDept(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateDepartment}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Department Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editDeptCode}
                    onChange={(e) => setEditDeptCode(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Department Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editDeptName}
                    onChange={(e) => setEditDeptName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="editDeptActive"
                    checked={editDeptActive}
                    onChange={(e) => setEditDeptActive(e.target.checked)}
                  />
                  <label htmlFor="editDeptActive" style={{ cursor: 'pointer', margin: 0 }}>
                    Active Department
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingDept(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT PROGRAM */}
      {editingProg && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Edit Degree Program: {editingProg.code}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingProg(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateProgram}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Parent Department</label>
                  <select
                    className="form-select"
                    value={editProgDeptId}
                    onChange={(e) => setEditProgDeptId(e.target.value)}
                    required
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.code} - {d.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Program Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editProgCode}
                    onChange={(e) => setEditProgCode(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Program Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editProgName}
                    onChange={(e) => setEditProgName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Total Semesters</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    className="form-input"
                    value={editProgSemesters}
                    onChange={(e) => setEditProgSemesters(parseInt(e.target.value) || 8)}
                    required
                  />
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="editProgActive"
                    checked={editProgActive}
                    onChange={(e) => setEditProgActive(e.target.checked)}
                  />
                  <label htmlFor="editProgActive" style={{ cursor: 'pointer', margin: 0 }}>
                    Active Degree Program
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingProg(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT COURSE */}
      {editingCourse && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Edit Course: {editingCourse.code}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingCourse(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateCourse}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Course Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editCourseCode}
                    onChange={(e) => setEditCourseCode(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Course Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editCourseName}
                    onChange={(e) => setEditCourseName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Academic Credits</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="20"
                    className="form-input"
                    value={editCourseCredits}
                    onChange={(e) => setEditCourseCredits(parseFloat(e.target.value) || 0)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Minimum Pass Percentage (%)</label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    max="100"
                    className="form-input"
                    value={editCoursePassPct}
                    onChange={(e) => setEditCoursePassPct(parseFloat(e.target.value) || 40)}
                    required
                  />
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="editCourseActive"
                    checked={editCourseActive}
                    onChange={(e) => setEditCourseActive(e.target.checked)}
                  />
                  <label htmlFor="editCourseActive" style={{ cursor: 'pointer', margin: 0 }}>
                    Active Course Offering
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingCourse(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT EXAMINATION SESSION */}
      {editingSession && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ Edit Examination Session: {editingSession.name}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingSession(null)}>✕</button>
            </div>
            <form onSubmit={handleUpdateSession}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Session Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editSessionName}
                    onChange={(e) => setEditSessionName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Academic Year</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editSessionYear}
                    onChange={(e) => setEditSessionYear(e.target.value)}
                    placeholder="e.g. 2025-2026"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Semester Number</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    className="form-input"
                    value={editSessionSem}
                    onChange={(e) => setEditSessionSem(parseInt(e.target.value) || 1)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Lifecycle Status</label>
                  <select
                    className="form-select"
                    value={editSessionStatus}
                    onChange={(e) => setEditSessionStatus(e.target.value)}
                    required
                  >
                    <option value="DRAFT">DRAFT</option>
                    <option value="MARKS_ENTRY_OPEN">MARKS_ENTRY_OPEN</option>
                    <option value="MARKS_LOCKED">MARKS_LOCKED</option>
                    <option value="CALCULATED">CALCULATED</option>
                    <option value="PUBLISHED">PUBLISHED</option>
                    <option value="ARCHIVED">ARCHIVED</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setEditingSession(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
