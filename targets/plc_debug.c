/*
 * DEBUGGER code
 * 
 * On "publish", when buffer is free, debugger stores arbitrary variables 
 * content into, and mark this buffer as filled
 * 
 * 
 * Buffer content is read asynchronously, (from non real time part), 
 * and then buffer marked free again.
 *  
 * 
 * */
#include "iec_types_all.h"
#include "POUS.h"
/*for memcpy*/
#include <string.h>
#include <stdio.h>

#define BUFFER_SIZE %(buffer_size)d
#define MAX_SUBSCRIBTION %(subscription_table_count)d

/* Atomically accessed variable for buffer state */
#define BUFFER_FREE 0
#define BUFFER_BUSY 1
static long buffer_state = BUFFER_FREE;

/* The buffer itself */
char debug_buffer[BUFFER_SIZE];

/* Buffer's cursor*/
static char* buffer_cursor = debug_buffer;
static unsigned int retain_offset = 0;
/***
 * Declare programs 
 **/
%(programs_declarations)s

/***
 * Declare global variables from resources and conf 
 **/
%(extern_variables_declarations)s

typedef void(*__for_each_variable_do_fp)(void*, __IEC_types_enum);
void __for_each_variable_do(__for_each_variable_do_fp fp)
{
%(for_each_variable_do_code)s
}

__IEC_types_enum __find_variable(unsigned int varindex, void ** varp)
{
    switch(varindex){
%(find_variable_case_code)s
     default:
      *varp = NULL;
      return UNKNOWN_ENUM;
    }
}

#define __BufferDebugDataIterator_case_t(TYPENAME) \
        case TYPENAME##_ENUM :\
            *flags = ((__IEC_##TYPENAME##_t *)varp)->flags;\
            *ptrvalue = &((__IEC_##TYPENAME##_t *)varp)->value;\
            break;

#define __BufferDebugDataIterator_case_p(TYPENAME)\
        case TYPENAME##_P_ENUM :\
            *flags = ((__IEC_##TYPENAME##_p *)varp)->flags;\
            if (*flags & __IEC_FORCE_FLAG)\
               *ptrvalue = &((__IEC_##TYPENAME##_p *)varp)->fvalue;\
            else\
               *ptrvalue = ((__IEC_##TYPENAME##_p *)varp)->value;\
            break;

void UnpackVar(void* varp, __IEC_types_enum vartype, void **ptrvalue, char *flags)
{
    /* find data to copy*/
    switch(vartype){
        ANY(__BufferDebugDataIterator_case_t)
        ANY(__BufferDebugDataIterator_case_p)
    default:
        break;
    }
}

void Remind(unsigned int offset, unsigned int count, void * p);

void RemindIterator(void* varp, __IEC_types_enum vartype)
{
    void *ptrvalue = NULL;
    char flags = 0;
    UnpackVar(varp, vartype, &ptrvalue, &flags);

    if(flags & __IEC_RETAIN_FLAG){
        USINT size = __get_type_enum_size(vartype);
        /* compute next cursor positon*/
        unsigned int next_retain_offset = retain_offset + size;
        /* if buffer not full */
        Remind(retain_offset, size, ptrvalue);
        /* increment cursor according size*/
        retain_offset = next_retain_offset;
    }
}

void __init_debug(void)
{
    /* init local static vars */
    buffer_cursor = debug_buffer;
    retain_offset = 0;
    buffer_state = BUFFER_FREE;
    /* Iterate over all variables to fill debug buffer */
    __for_each_variable_do(RemindIterator);
    retain_offset = 0;
}

extern void InitiateDebugTransfer(void);

extern unsigned long __tick;

void __cleanup_debug(void)
{
    buffer_cursor = debug_buffer;
    InitiateDebugTransfer();
}

void __retrieve_debug(void)
{
}

void DoDebug(void *ptrvalue, char flags, USINT size)
{
    /* compute next cursor positon*/
    char* next_cursor = buffer_cursor + size;
    /* if buffer not full */
    if(next_cursor <= debug_buffer + BUFFER_SIZE)
    {
        /* copy data to the buffer */
        memcpy(buffer_cursor, ptrvalue, size);
        /* increment cursor according size*/
        buffer_cursor = next_cursor;
    }else{
        /*TODO : signal overflow*/
    }
}

void Retain(unsigned int offset, unsigned int count, void * p);
void DoRetain(void *ptrvalue, char flags, USINT size){
    /* compute next cursor positon*/
    unsigned int next_retain_offset = retain_offset + size;
    /* if buffer not full */
    Retain(retain_offset, size, ptrvalue);
    /* increment cursor according size*/
    retain_offset = next_retain_offset;
}

void BufferDebugDataIterator(void* varp, __IEC_types_enum vartype)
{
    void *ptrvalue = NULL;
    char flags = 0;
    UnpackVar(varp, vartype, &ptrvalue, &flags);
    /* For optimization purpose we do retain and debug in the same pass */
    if(flags & (__IEC_DEBUG_FLAG | __IEC_RETAIN_FLAG)){
        USINT size = __get_type_enum_size(vartype);
        if(flags & __IEC_DEBUG_FLAG){
            DoDebug(ptrvalue, flags, size);
        }
        if(flags & __IEC_RETAIN_FLAG){
            DoRetain(ptrvalue, flags, size);
        }
    }
}

void RetainIterator(void* varp, __IEC_types_enum vartype)
{
    void *ptrvalue = NULL;
    char flags = 0;
    UnpackVar(varp, vartype, &ptrvalue, &flags);

    if(flags & __IEC_RETAIN_FLAG){
        USINT size = __get_type_enum_size(vartype);
        DoRetain(ptrvalue, flags, size);
    }
}

extern int TryEnterDebugSection(void);
extern long AtomicCompareExchange(long*, long, long);
extern void LeaveDebugSection(void);

void __publish_debug(void)
{
    retain_offset = 0;
    /* Check there is no running debugger re-configuration */
    if(TryEnterDebugSection()){
        /* Lock buffer */
        long latest_state = AtomicCompareExchange(
            &buffer_state,
            BUFFER_FREE,
            BUFFER_BUSY);
            
        /* If buffer was free */
        if(latest_state == BUFFER_FREE)
        {
            /* Reset buffer cursor */
            buffer_cursor = debug_buffer;
            /* Iterate over all variables to fill debug buffer */
            __for_each_variable_do(BufferDebugDataIterator);
            
            /* Leave debug section,
             * Trigger asynchronous transmission 
             * (returns immediately) */
            InitiateDebugTransfer(); /* size */
        }
        LeaveDebugSection();
    }else{
        /* when not debugging, do only retain */
        __for_each_variable_do(RetainIterator);
    }
}

#define __RegisterDebugVariable_case_t(TYPENAME) \
        case TYPENAME##_ENUM :\
            ((__IEC_##TYPENAME##_t *)varp)->flags |= flags;\
            if(force)\
             ((__IEC_##TYPENAME##_t *)varp)->value = *((TYPENAME *)force);\
            break;
#define __RegisterDebugVariable_case_p(TYPENAME)\
        case TYPENAME##_P_ENUM :\
            ((__IEC_##TYPENAME##_p *)varp)->flags |= flags;\
            if(force)\
             ((__IEC_##TYPENAME##_p *)varp)->fvalue = *((TYPENAME *)force);\
            break;
void RegisterDebugVariable(int idx, void* force)
{
    void *varp = NULL;
    unsigned char flags = force ? __IEC_DEBUG_FLAG | __IEC_FORCE_FLAG : __IEC_DEBUG_FLAG;
    switch(__find_variable(idx, &varp)){
        ANY(__RegisterDebugVariable_case_t)
        ANY(__RegisterDebugVariable_case_p)
    default:
        break;
    }
}

#define __ResetDebugVariablesIterator_case_t(TYPENAME) \
        case TYPENAME##_ENUM :\
            ((__IEC_##TYPENAME##_t *)varp)->flags &= ~(__IEC_DEBUG_FLAG|__IEC_FORCE_FLAG);\
            break;

#define __ResetDebugVariablesIterator_case_p(TYPENAME)\
        case TYPENAME##_P_ENUM :\
            ((__IEC_##TYPENAME##_p *)varp)->flags &= ~(__IEC_DEBUG_FLAG|__IEC_FORCE_FLAG);\
            break;

void ResetDebugVariablesIterator(void* varp, __IEC_types_enum vartype)
{
    /* force debug flag to 0*/
    switch(vartype){
        ANY(__ResetDebugVariablesIterator_case_t)
        ANY(__ResetDebugVariablesIterator_case_p)
    default:
        break;
    }
}

void ResetDebugVariables(void)
{
    __for_each_variable_do(ResetDebugVariablesIterator);
}

void FreeDebugData(void)
{
    /* atomically mark buffer as free */
    long latest_state;
    latest_state = AtomicCompareExchange(
        &buffer_state,
        BUFFER_BUSY,
        BUFFER_FREE);
}
int WaitDebugData(unsigned long *tick);
/* Wait until debug data ready and return pointer to it */
int GetDebugData(unsigned long *tick, unsigned long *size, void **buffer){
    int wait_error = WaitDebugData(tick);
    if(!wait_error){
        *size = buffer_cursor - debug_buffer;
        *buffer = debug_buffer;
    }
    return wait_error;
}

